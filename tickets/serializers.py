from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attachment, Comment, Ticket, TicketEvent

MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
ALLOWED_ATTACHMENT_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "log", "csv", "zip",
}

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


class AttachmentSerializer(serializers.ModelSerializer):
    """A file on a ticket. The response never exposes the storage path — files
    are fetched through the download endpoint."""

    uploaded_by_username = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)

    def get_uploaded_by_username(self, obj) -> str | None:
        return obj.uploaded_by.username if obj.uploaded_by else None

    class Meta:
        model = Attachment
        fields = (
            "id",
            "file",
            "original_name",
            "size",
            "uploaded_by",
            "uploaded_by_username",
            "created_at",
        )
        read_only_fields = ("original_name", "size", "uploaded_by")

    def validate_file(self, value):
        if value.size > MAX_ATTACHMENT_BYTES:
            raise serializers.ValidationError("attachments are limited to 5 MB")
        extension = value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
        if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))
            raise serializers.ValidationError(f"file type not allowed (allowed: {allowed})")
        return value

    def create(self, validated_data):
        upload = validated_data["file"]
        validated_data["original_name"] = upload.name
        validated_data["size"] = upload.size
        return super().create(validated_data)
