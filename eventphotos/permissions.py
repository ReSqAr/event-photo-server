from rest_framework import permissions

from eventphotos.models import UserAuthenticatedForEvent


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Otherwise the user has to be authenticated.
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow the user themself to edit the user object.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # do not let the user create new users
        if request.method == 'POST':
            return False

        # Otherwise the user has to be authenticated.
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


def IsUserOrAdminConstructor(_get_owner):
    class IsUserOrAdmin(permissions.BasePermission):
        """
        Object-level permission to only allow the user themself to edit the user object.
        """

        def has_permission(self, request, view):
            # Do not let the user create new objects.
            if request.method == 'POST':
                return False

            # Otherwise the user has to be the super user.
            return request.user.is_superuser

        def has_object_permission(self, request, view, obj):
            if request.user.is_superuser:
                return True
            else:
                return _get_owner(obj) == request.user

    return IsUserOrAdmin


def IsOwnerOrAuthorisedForEventConstructor(_get_owner, _get_event):
    class IsOwnerOrAuthorisedForEvent(permissions.BasePermission):
        """
        Object-level permission to only allow the owner to edit the object
        and authorised users to view it.
        """

        def has_permission(self, request, view):
            # We deal with read permissions in the filter statement.
            if request.method in permissions.SAFE_METHODS:
                return True

            # WARNING: object creation has to be checked against event authorisation before saving
            if request.method == 'POST':
                return True

            # Otherwise the user has to be the super user.
            return request.user.is_superuser

        def has_object_permission(self, request, view, obj):
            if request.user.is_superuser:
                # super user may to everything
                return True
            elif _get_owner(obj) == request.user:
                # the owner may do everything
                return True
            else:
                if request.method in permissions.SAFE_METHODS:
                    # an authorised user may view it
                    user = request.user
                    event = _get_event(obj)
                    return UserAuthenticatedForEvent.is_user_authenticated_for_event(user, event)
                else:
                    return False

    return IsOwnerOrAuthorisedForEvent
