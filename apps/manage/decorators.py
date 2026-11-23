from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import render


def staff_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff member.
    Returns HTTP 403 for non-staff on every /manage/ route (Requirement A10).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return render(request, 'manage/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
