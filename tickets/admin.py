from django.contrib import admin

from .models import Profile, SlaPolicy, Ticket

admin.site.register(Profile)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "assignee", "sla_due_at")
    list_filter = ("status", "priority")


@admin.register(SlaPolicy)
class SlaPolicyAdmin(admin.ModelAdmin):
    list_display = ("priority", "hours", "updated_by", "updated_at")
