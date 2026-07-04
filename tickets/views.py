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
        """Assign the ticket to a user (open -> assigned)."""
        ticket = self.get_object()
        assignee_id = request.data.get("assignee")
        if not assignee_id:
            return Response({"detail": "assignee is required"}, status=400)
        assignee = get_object_or_404(User, pk=assignee_id)
        try:
            ticket.assign(assignee, actor=request.user)
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        """Escalate the ticket, with an optional note."""
        ticket = self.get_object()
        try:
            ticket.escalate(actor=request.user, note=request.data.get("note", ""))
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark the ticket resolved (assigned/escalated -> resolved)."""
        ticket = self.get_object()
        try:
            ticket.resolve(actor=request.user)
        except TransitionError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Close a resolved ticket."""
        ticket = self.get_object()
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
            serializer.save(ticket=ticket, author=request.user)
            return Response(serializer.data, status=201)
        comments = ticket.comments.all()
        if role(request.user) == "requester":
            comments = comments.filter(is_internal=False)
        return Response(CommentSerializer(comments, many=True).data)
