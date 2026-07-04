from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, Ticket, TicketEvent

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TicketSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = TicketEvent
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "ticket", "author", "body", "is_internal", "created_at")
        read_only_fields = ("ticket", "author")
