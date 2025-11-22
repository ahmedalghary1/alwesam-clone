from django.urls import path
from . import views


app_name = "accounts"

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password_view, name='forgot-password'),
    path('verify-code/', views.verify_code_view, name='verify-code'),
    path('reset-password/', views.reset_password_view, name='reset-password'),
    path('resend-code/', views.resend_code_view, name='resend-code'),
    
    # Admin actions
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
