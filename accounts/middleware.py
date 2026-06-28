from django.shortcuts import redirect
from django.urls import reverse

# Ces vues restent accessibles même en attente d'approbation
ALLOWED_URL_NAMES = ['dashboard', 'deconnexion', 'mark_notification_read', 'notifications']


class PendingApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Un membre dont la demande est encore "pending" est restreint
            pending_request = request.user.join_requests.filter(status='pending').first()
            if pending_request:
                resolved_name = getattr(request.resolver_match, 'url_name', None)
                if resolved_name not in ALLOWED_URL_NAMES:
                    return redirect('dashboard')

        response = self.get_response(request)
        return response
