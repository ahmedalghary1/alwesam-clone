from django.contrib.auth.models import AbstractUser , BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random



# ========== 1. UserManager مخصص ==========
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("يجب إدخال بريد إلكتروني صالح")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('المشرف يجب أن يكون is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('المشرف يجب أن يكون is_superuser=True')

        return self.create_user(email, password, **extra_fields)






class CustomUser(AbstractUser):
    username = None  # نحذف الحقل الافتراضي
    email = models.EmailField(unique=True)  # نستخدم الإيميل بدلًا منه

    image = models.ImageField(upload_to='user_images/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True, max_length=500)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(blank=True, null=True)

    USERNAME_FIELD = 'email'      # تحديد الإيميل كحقل تسجيل دخول
    REQUIRED_FIELDS = []          # لا نطلب حقول إضافية أثناء إنشاء المستخدم من CLI
    objects = CustomUserManager()  # تعيين مدير المستخدم المخصص 

    def __str__(self):
        return self.email


# ========== 2. نموذج رمز استعادة كلمة المرور ==========
class PasswordResetCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """التحقق من أن الرمز ما زال صالحاً"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_code():
        """توليد رمز من 6 أرقام"""
        return str(random.randint(100000, 999999))
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"
