from rest_framework import permissions


def role(user):
    return getattr(getattr(user, "profile", None), "role", None)


class IsStaffReadManagerWrite(permissions.BasePermission):
    """Agents and managers can read; only managers can create/edit/delete."""

    def has_permission(self, request, view):
        r = role(request.user)
        if request.method in permissions.SAFE_METHODS:
            return r in ("agent", "manager")
        return r == "manager"


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
