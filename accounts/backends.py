from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address
    or phone number instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email/phone and password.
        'username' parameter can contain either email or phone number.
        """
        # Support both 'username' and 'email' parameters
        identifier = kwargs.get('email', username)
        
        if identifier is None or password is None:
            return None
        
        user = None
        
        # Try to find user by email first (case-insensitive)
        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            # If not found by email, try phone number
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                # Run the default password hasher once to reduce timing
                # difference between existing and non-existing users
                User().set_password(password)
                return None
        
        # Check password
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None
