from rest_framework import permissions


def role(user):
    return getattr(getattr(user, "profile", None), "role", None)


class IsManagerOrAssignedOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        r = role(request.user)
        if r == "manager":
            return True
        if r == "agent":
            return obj.assignee_id == request.user.id
        return obj.requester_id == request.user.id
