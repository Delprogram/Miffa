from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def approved_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'member' and not request.user.family:
            from .models import JoinRequest
            has_pending = JoinRequest.objects.filter(user=request.user, status='pending').exists()
            if has_pending:
                messages.warning(request, "Votre demande d'adhésion est en attente d'approbation.")
                return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def guest_permission_required(module):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            target_family = request.user.family  # la famille qu'il consulte par défaut

            # Si ce n'est pas sa famille principale, vérifie s'il y a un accès invité
            if request.user.family is None or request.user.role == 'guest':
                pass  # cas à affiner selon comment tu navigues entre familles

            if request.user.role == 'guest':
                access = request.user.guest_accesses.filter(family=target_family, is_active=True).first()
                if not access or not access.has_permission(module):
                    messages.error(request, "Vous n'avez pas accès à cette section en tant qu'invité.")
                    return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
