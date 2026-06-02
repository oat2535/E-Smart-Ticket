from .models import AccessRequest
from .utils import get_user_role

def pending_approvals_count(request):
    role = get_user_role(request.user)
    
    if role == 'manager':
        count = AccessRequest.systems.through.objects.filter(accessrequest__status='pending_manager').count()
        return {'pending_approval_count': count, 'user_role': role, 'can_approve_requests': True}
    elif role in ['it', 'admin']:
        count = AccessRequest.systems.through.objects.filter(accessrequest__status__in=['pending_manager', 'pending_it']).count()
        return {'pending_approval_count': count, 'user_role': role, 'can_approve_requests': True}
        
    return {'can_approve_requests': False, 'user_role': role}
