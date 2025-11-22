from django.shortcuts import render, get_object_or_404

from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.contrib import messages



from django.urls import reverse

from .models import CustomUser, PasswordResetCode
from .email_utils import send_verification_code_email, send_welcome_email




from django.contrib.auth.decorators import login_required



def register_view(request):
    if request.method == 'POST':
        # Get form data - no username, only email
        first_name = request.POST.get('username', '')  # Using 'username' field as full name from form
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password')
        confirm = request.POST.get('confirmPassword')

        # Validation: Check password match
        if password != confirm:
            messages.error(request, '❌ كلمتا المرور غير متطابقتين.')
            return redirect('accounts:register')

        # Validation: Check email exists - silently redirect without error message
        if CustomUser.objects.filter(email=email).exists():
            # Don't show error message, just redirect to clear form
            return redirect('accounts:register')

        # Validation: Check password length
        if len(password) < 8:
            messages.error(request, '⚠️ كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل.')
            return redirect('accounts:register')

        try:
            # Create user - CustomUser uses email as USERNAME_FIELD
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
            )
            
            # Set additional fields
            user.first_name = first_name
            user.phone_number = phone_number
            user.save()

            # Send welcome email
            try:
                send_welcome_email(user)
            except Exception as e:
                print(f"Failed to send welcome email: {e}")
                # Don't block registration if email fails

            messages.success(request, '✅ تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول.')
            return redirect('accounts:login')
            
        except Exception as e:
            messages.error(request, f'❌ حدث خطأ أثناء إنشاء الحساب: {str(e)}')
            return redirect('accounts:register')

    # GET request - show registration form
    return render(request, 'accounts/register.html')

def login_view(request):
    """
    Handle user login with email and password.
    """
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect(reverse('home'))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Validate input
        if not email or not password:
            messages.error(request, '⚠️ يرجى إدخال البريد الإلكتروني وكلمة المرور.')
            return render(request, 'accounts/login_page.html')

        # Authenticate using custom EmailBackend
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Login successful
            login(request, user)
            messages.success(request, f'✅ مرحباً بك {user.first_name or ""}!')
            
            # Redirect to 'next' parameter or home page
            next_url = request.GET.get('next', reverse('home'))
            return redirect(next_url)
        else:
            # Login failed
            messages.error(request, '❌ البريد الإلكتروني أو كلمة المرور غير صحيحة.')
    
    return render(request, 'accounts/login_page.html')



from django.contrib.auth import logout

def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.success(request, '✅ تم تسجيل الخروج بنجاح.')
    return redirect('home')


@login_required
def profile_view(request):
    """
    Display and edit user profile.
    """
    user = request.user
    
    if request.method == 'POST':
        # Get updated values
        new_phone = request.POST.get('phone_number', '').strip()
        
        # Check if phone number is being changed and if it's already taken by another user
        if new_phone and new_phone != user.phone_number:
            if CustomUser.objects.filter(phone_number=new_phone).exclude(id=user.id).exists():
                messages.error(request, '⚠️ رقم الهاتف هذا مستخدم بالفعل من قبل مستخدم آخر.', extra_tags='danger')
                return redirect('accounts:profile')
        
        # Update user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = new_phone if new_phone else user.phone_number
        user.address = request.POST.get('address', user.address)
        
        # Handle profile image upload
        if 'image' in request.FILES:
            user.image = request.FILES['image']
        
        user.save()
        messages.success(request, '✅ تم تحديث الملف الشخصي بنجاح.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {'user': user})


@login_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "✅ تم حذف المستخدم بنجاح.")
    return redirect('/admin/')



@login_required
def edit_profile(request):
    """
    Handle profile edit via AJAX or form submission.
    This is kept for backward compatibility but profile_view is preferred.
    """
    user = request.user

    if request.method == 'POST':
        # Get updated values
        new_phone = request.POST.get('phone_number', '').strip()
        
        # Check if phone number is being changed and if it's already taken by another user
        if new_phone and new_phone != user.phone_number:
            if CustomUser.objects.filter(phone_number=new_phone).exclude(id=user.id).exists():
                messages.error(request, '⚠️ رقم الهاتف هذا مستخدم بالفعل من قبل مستخدم آخر.', extra_tags='danger')
                return redirect('accounts:profile')
        
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = new_phone if new_phone else user.phone_number
        user.address = request.POST.get('address', user.address)
        user.save()
        messages.success(request, "✅ تم تحديث الملف الشخصي بنجاح.")
        return redirect('accounts:profile')
    
    return redirect('accounts:profile')


# ========== Password Reset Views ==========

def forgot_password_view(request):
    """
    صفحة طلب استعادة كلمة المرور - إدخال البريد الإلكتروني
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Check if email exists
        try:
            user = CustomUser.objects.get(email=email)
            
            # Generate verification code
            code = PasswordResetCode.generate_code()
            
            # Create reset code entry
            reset_code = PasswordResetCode.objects.create(
                user=user,
                code=code
            )
            
            # Send email with code
            try:
                send_verification_code_email(user, code)
                messages.success(request, '✅ تم إرسال رمز التحقق إلى بريدك الإلكتروني.')
                # Store email in session to use in next step
                request.session['reset_email'] = email
                return redirect('accounts:verify-code')
            except Exception as e:
                messages.error(request, f'❌ فشل إرسال البريد الإلكتروني: {str(e)}')
                reset_code.delete()
                
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.error(request, '⚠️ إذا كان البريد الإلكتروني موجوداً، سيتم إرسال رمز التحقق.')
    
    return render(request, 'accounts/forgot_password.html')


def verify_code_view(request):
    """
    صفحة التحقق من رمز الاستعادة
    """
    email = request.session.get('reset_email')
    
    if not email:
        messages.error(request, '⚠️ يجب طلب استعادة كلمة المرور أولاً.')
        return redirect('accounts:forgot-password')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        try:
            user = CustomUser.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(
                user=user,
                code=code
            ).order_by('-created_at').first()
            
            if reset_code and reset_code.is_valid():
                # Code is valid, proceed to reset password
                request.session['reset_code_id'] = reset_code.id
                return redirect('accounts:reset-password')
            else:
                messages.error(request, '❌ الرمز غير صحيح أو منتهي الصلاحية.')
                
        except CustomUser.DoesNotExist:
            messages.error(request, '❌ حدث خطأ، يرجى المحاولة مرة أخرى.')
    
    return render(request, 'accounts/verify_code.html', {'email': email})


def reset_password_view(request):
    """
    صفحة إنشاء كلمة مرور جديدة
    """
    reset_code_id = request.session.get('reset_code_id')
    
    if not reset_code_id:
        messages.error(request, '⚠️ يجب التحقق من الرمز أولاً.')
        return redirect('accounts:forgot-password')
    
    try:
        reset_code = PasswordResetCode.objects.get(id=reset_code_id)
        
        if not reset_code.is_valid():
            messages.error(request, '❌ انتهت صلاحية الرمز، يرجى طلب رمز جديد.')
            return redirect('accounts:forgot-password')
        
        if request.method == 'POST':
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validation
            if password != confirm_password:
                messages.error(request, '❌ كلمتا المرور غير متطابقتين.')
            elif len(password) < 8:
                messages.error(request, '⚠️ كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل.')
            else:
                # Update password
                user = reset_code.user
                user.set_password(password)
                user.save()
                
                # Mark code as used
                reset_code.is_used = True
                reset_code.save()
                
                # Clear session
                request.session.pop('reset_email', None)
                request.session.pop('reset_code_id', None)
                
                messages.success(request, '✅ تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.')
                return redirect('accounts:login')
        
        return render(request, 'accounts/reset_password.html')
        
    except PasswordResetCode.DoesNotExist:
        messages.error(request, '❌ حدث خطأ، يرجى المحاولة مرة أخرى.')
        return redirect('accounts:forgot-password')


def resend_code_view(request):
    """
    إعادة إرسال رمز التحقق
    """
    email = request.session.get('reset_email')
    
    if not email:
        messages.error(request, '⚠️ يجب طلب استعادة كلمة المرور أولاً.')
        return redirect('accounts:forgot-password')
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Generate new code
        code = PasswordResetCode.generate_code()
        
        # Create new reset code entry
        reset_code = PasswordResetCode.objects.create(
            user=user,
            code=code
        )
        
        # Send email
        try:
            send_verification_code_email(user, code)
            messages.success(request, '✅ تم إعادة إرسال رمز التحقق.')
        except Exception as e:
            messages.error(request, f'❌ فشل إرسال البريد الإلكتروني: {str(e)}')
            reset_code.delete()
            
    except CustomUser.DoesNotExist:
        messages.error(request, '❌ حدث خطأ.')
    
    return redirect('accounts:verify-code')

