from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class TransitionError(Exception):
    pass


ALLOWED = {
    ("open", "assigned"),
    ("open", "escalated"),
    ("assigned", "resolved"),
    ("assigned", "escalated"),
    ("escalated", "resolved"),
    ("resolved", "closed"),
}


class Profile(models.Model):
    class Role(models.TextChoices):
        REQUESTER = "requester", "Requester"
        AGENT = "agent", "Agent"
        MANAGER = "manager", "Manager"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REQUESTER)

    def __str__(self):
        return f"{self.user} ({self.role})"


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ASSIGNED = "assigned", "Assigned"
        ESCALATED = "escalated", "Escalated"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_opened"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_assigned",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    category = models.CharField(max_length=40, default="other")
    sla_due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["sla_due_at"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    def _transition(self, to_status, actor=None, note=""):
        with transaction.atomic():
            # Lock the row and re-read status so concurrent transitions (two agents,
            # or an agent racing the SLA job) serialize instead of double-firing.
            current = (
                Ticket.objects.select_for_update().values_list("status", flat=True).get(pk=self.pk)
            )
            if (current, to_status) not in ALLOWED:
                raise TransitionError(f"cannot go {current} -> {to_status}")
            TicketEvent.objects.create(
                ticket=self,
                actor=actor,
                from_status=current,
                to_status=to_status,
                note=note,
            )
            self.status = to_status
            # Save only status so a concurrent write to priority/title/assignee on
            # a stale in-memory copy of this ticket isn't reverted by a full save.
            self.save(update_fields=["status"])

    def assign(self, assignee, actor=None):
        self._transition("assigned", actor)  # guard runs first
        self.assignee = assignee
        self.save(update_fields=["assignee"])

    def escalate(self, actor=None, note=""):
        self._transition("escalated", actor, note)
        self.escalated_at = timezone.now()
        self.save(update_fields=["escalated_at"])

    def resolve(self, actor=None):
        self._transition("resolved", actor)
        self.resolved_at = timezone.now()
        self.save(update_fields=["resolved_at"])

    def close(self, actor=None):
        self._transition("closed", actor)
        self.closed_at = timezone.now()
        self.save(update_fields=["closed_at"])


class TicketEvent(models.Model):
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"ticket {self.ticket_id}: {self.from_status} -> {self.to_status}"


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"comment by {self.author} on ticket {self.ticket_id}"


class CannedResponse(models.Model):
    """A reusable reply template for staff. Managers curate the library; agents
    read it and paste a template into a comment (the API stores plain text, so
    'using' one is just posting its body)."""

    title = models.CharField(max_length=200, unique=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
