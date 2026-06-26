from .models import RelationRequest
from .models import Notification, RelationRequest

def pending_relation_requests(request):
    if request.user.is_authenticated:
        count = RelationRequest.objects.filter(to_user=request.user, status='pending').count()
        return {'pending_relation_count': count}
    return {'pending_relation_count': 0}


def pending_relation_requests(request):
    if request.user.is_authenticated:
        relation_count = RelationRequest.objects.filter(to_user=request.user, status='pending').count()
        notif_count    = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'pending_relation_count': relation_count,
            'unread_notif_count':     notif_count,
        }
    return {'pending_relation_count': 0, 'unread_notif_count': 0}