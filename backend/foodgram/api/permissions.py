from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Права админа или метод безопасный."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_superuser)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_superuser)


class IsAuthenticatedOrSignUp(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return (
            (request.method in permissions.SAFE_METHODS
             and request.user.is_authenticated)
            or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return (
            (request.method in permissions.SAFE_METHODS
             and request.user.is_authenticated)
            or request.user.is_superuser
        )


class RecipePermissions(permissions.BasePermission):
    """Автор или авторизованный."""
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user == obj.author
            or request.user.is_superuser
        )
