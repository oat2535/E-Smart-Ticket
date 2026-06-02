def get_user_role(user):
    if not user.is_authenticated:
        return 'user'
    if getattr(user, 'is_superuser', False) or getattr(user, 'username', '') == 'admin':
        return 'admin'
    
    if hasattr(user, 'position') and user.position:
        pos_id = user.position.id
        pos_name = user.position.name.lower()
        if pos_id == 1 or 'ผู้จัดการ' in pos_name or 'manager' in pos_name:
            return 'manager'
        if pos_id == 3 or 'it' in pos_name or 'ไอที' in pos_name:
            return 'it'
        if pos_id == 4 or 'ผู้ดูแลระบบ' in pos_name or 'admin' in pos_name:
            return 'admin'
            
    if getattr(user, 'is_staff', False):
        return 'admin'
        
    return 'user'
