from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import CannedResponse, Comment, Ticket, TicketEvent

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Create a user account; the password is write-only and stored hashed."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    """The authenticated user and their role."""

    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")


class TicketSerializer(serializers.ModelSerializer):
    """A ticket. Status and its timestamps only change via the action endpoints."""

    requester_username = serializers.CharField(source="requester.username", read_only=True)
    assignee_username = serializers.SerializerMethodField()

    def get_assignee_username(self, obj) -> str | None:
        return obj.assignee.username if obj.assignee else None

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = (
            "requester",
            "assignee",
            "status",
            "sla_due_at",
            "escalated_at",
            "resolved_at",
            "closed_at",
        )


class TicketEventSerializer(serializers.ModelSerializer):
    """One audit row per status change: actor, from/to status, optional note."""

    actor_username = serializers.SerializerMethodField()

    def get_actor_username(self, obj) -> str | None:
        return obj.actor.username if obj.actor else None

    class Meta:
        model = TicketEvent
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    """A comment on a ticket; internal comments are hidden from requesters."""

    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "ticket", "author", "author_username", "body", "is_internal", "created_at")
        read_only_fields = ("ticket", "author")


class CannedResponseSerializer(serializers.ModelSerializer):
    """A reusable staff reply template."""

    created_by_username = serializers.SerializerMethodField()

    def get_created_by_username(self, obj) -> str | None:
        return obj.created_by.username if obj.created_by else None

    class Meta:
        model = CannedResponse
        fields = ("id", "title", "body", "created_by", "created_by_username", "updated_at")
        read_only_fields = ("created_by",)
