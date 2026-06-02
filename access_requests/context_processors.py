from .models import AccessRequest

def pending_approvals_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or request.user.username == 'admin'):
        count = AccessRequest.systems.through.objects.filter(accessrequest__status__in=['pending_manager', 'pending_it']).count()
        return {'pending_approval_count': count}
    return {}
