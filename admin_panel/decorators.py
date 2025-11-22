from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def admin_required(view_func):
    """
    Decorator to check if user is staff/admin.
    Redirects to login if not authenticated or to home if not staff.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, '⚠️ يجب تسجيل الدخول أولاً.')
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        
        if not request.user.is_staff:
            messages.error(request, '❌ ليس لديك صلاحية الوصول إلى هذه الصفحة.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
