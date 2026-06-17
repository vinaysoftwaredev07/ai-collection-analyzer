"""
Access control decorators for the strategy app.
Provides role-based access enforcement on top of Django's built-in auth.
"""
import functools
import logging

from django.http import HttpResponseForbidden

from .models import UserProfile

logger = logging.getLogger(__name__)


def get_user_role(user):
    """
    Safely retrieve the role for a given user.
    Returns 'agent' as the default if no profile exists.
    """
    try:
        return user.profile.role
    except (UserProfile.DoesNotExist, AttributeError):
        return 'agent'


def role_required(allowed_roles):
    """
    Decorator that restricts a view to users whose profile role is in `allowed_roles`.
    Must be used AFTER @login_required so that request.user is authenticated.

    Usage:
        @login_required
        @role_required(['supervisor'])
        def admin_only_view(request):
            ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = get_user_role(request.user)
            if user_role not in allowed_roles:
                logger.warning(
                    "Access denied: user=%s role=%s tried to access %s (allowed: %s)",
                    request.user.username, user_role,
                    request.path, allowed_roles,
                )
                return HttpResponseForbidden(
                    "You do not have permission to access this resource."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
