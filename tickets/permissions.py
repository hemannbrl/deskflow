from rest_framework import permissions


def role(user):
    return getattr(getattr(user, "profile", None), "role", None)


class IsManagerOrAssignedOrOwner(permissions.BasePermission):
    """Managers touch everything; agents their assigned tickets plus the unassigned
    queue; requesters their own. Role rules per action live in the viewset."""

    def has_object_permission(self, request, view, obj):
        r = role(request.user)
        if r == "manager":
            return True
        if r == "agent":
            return obj.assignee_id in (request.user.id, None)
        return obj.requester_id == request.user.id
