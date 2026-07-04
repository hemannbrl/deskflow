from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket, TransitionError
from .permissions import IsManagerOrAssignedOrOwner, role
from .serializers import (
    CommentSerializer,
    MeSerializer,
    RegisterSerializer,
    TicketEventSerializer,
    TicketSerializer,
)
from .sla import due_at

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """The authenticated user's account and role."""

    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class TicketViewSet(viewsets.ModelViewSet):
    """Tickets, scoped by role: requesters see their own, agents their queue, managers all."""

    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAssignedOrOwner]
    http_method_names = ["get", "post", "patch", "head", "options"]  # no PUT/DELETE

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # schema generation has no user
            return Ticket.objects.none()
        user = self.request.user
        r = role(user)
        if r == "manager":
            return Ticket.objects.all()
        if r == "agent":
            return Ticket.objects.filter(Q(assignee=user) | Q(assignee__isnull=True))
        return Ticket.objects.filter(requester=user)

    def perform_create(self, serializer):
        ticket = serializer.save(requester=self.request.user)
        ticket.sla_due_at = due_at(ticket.priority)
        ticket.save(update_fields=["sla_due_at"])

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign the ticket (open -> assigned). Managers assign anyone; agents
        may only claim a ticket for themselves."""
        ticket = self.get_object()
        assignee_id = request.data.get("assignee")
        if not assignee_id:
            return Response({"detail": "assignee is required"}, status=400)
        r = role(request.user)
        if r == "agent":
            if str(assignee_id) != str(request.user.id):
                return Response(
                    {"detail": "agents may only assign tickets to themselves"}, status=403
                )
        elif r != "manager":
            return Response({"detail": "only agents and managers can assign tickets"}, status=403)
        assignee = get_object_or_404(User, pk=assignee_id)
        try:
            ticket.assign(assignee, actor=request.user)
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        """Escalate the ticket, with an optional note. Managers only — automatic
        escalation is the SLA job's."""
        ticket = self.get_object()
        if role(request.user) != "manager":
            return Response({"detail": "only managers can escalate tickets"}, status=403)
        try:
            ticket.escalate(actor=request.user, note=request.data.get("note", ""))
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark the ticket resolved (assigned/escalated -> resolved). The assigned
        agent or a manager."""
        ticket = self.get_object()
        r = role(request.user)
        if not (r == "manager" or (r == "agent" and ticket.assignee_id == request.user.id)):
            return Response(
                {"detail": "only the assigned agent or a manager can resolve"}, status=403
            )
        try:
            ticket.resolve(actor=request.user)
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Close a resolved ticket. The requester confirming their fix, or a manager."""
        ticket = self.get_object()
        if not (role(request.user) == "manager" or ticket.requester_id == request.user.id):
            return Response({"detail": "only the requester or a manager can close"}, status=403)
        try:
            ticket.close(actor=request.user)
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        """The ticket's audit history, oldest first."""
        events = self.get_object().events.all()
        return Response(TicketEventSerializer(events, many=True).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        """List the comment thread (internal notes hidden from requesters) or add a comment."""
        ticket = self.get_object()
        if request.method == "POST":
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data.get("is_internal") and role(request.user) not in (
                "agent",
                "manager",
            ):
                return Response({"detail": "internal notes are restricted to staff"}, status=403)
            serializer.save(ticket=ticket, author=request.user)
            return Response(serializer.data, status=201)
        comments = ticket.comments.all()
        if role(request.user) == "requester":
            comments = comments.filter(is_internal=False)
        return Response(CommentSerializer(comments, many=True).data)
