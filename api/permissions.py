from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        return False


class IsProfileOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # For StudentProfile objects
        return obj.user == request.user


class IsRoomMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user's profile is in the room members
        try:
            user_profile = request.user.profile
            return obj.members.filter(id=user_profile.id).exists()
        except:
            return False


class IsNotificationRecipient(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            return obj.recipient.user == request.user
        except:
            return False


class IsMatchParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            user_profile = request.user.profile
            return obj.student_a == user_profile or obj.student_b == user_profile
        except:
            return False

