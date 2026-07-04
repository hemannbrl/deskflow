from django.contrib import admin

from .models import Profile, Ticket

admin.site.register(Profile)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "assignee", "sla_due_at")
    list_filter = ("status", "priority")
