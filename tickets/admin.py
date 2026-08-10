from django.contrib import admin

from .models import CannedResponse, Profile, Ticket

admin.site.register(Profile)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "assignee", "sla_due_at")
    list_filter = ("status", "priority")


@admin.register(CannedResponse)
class CannedResponseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "updated_at")
    search_fields = ("title", "body")
