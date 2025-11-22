from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_verification_code_email(user, code):
    """
    إرسال رمز التحقق إلى البريد الإلكتروني للمستخدم
    """
    subject = 'رمز استعادة كلمة المرور - متجر الوسام للأدوات الكهربائية'
    
    # Create HTML message
    html_message = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Cairo', 'Segoe UI', Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
                direction: rtl;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 900;
            }}
            .highlight {{
                color: #FFD700;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .code-box {{
                background-color: #f8f9fa;
                border: 3px dashed #FFD700;
                border-radius: 10px;
                padding: 30px;
                margin: 30px 0;
            }}
            .code {{
                font-size: 48px;
                font-weight: 900;
                color: #000000;
                letter-spacing: 10px;
            }}
            .warning {{
                background-color: #fff3cd;
                border-right: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                text-align: right;
            }}
            .footer {{
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 20px;
                text-align: center;
                font-size: 14px;
            }}
            .footer a {{
                color: #FFD700;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ الأدوات <span class="highlight">الكهربائية</span></h1>
                <p>متجرك الموثوق للأدوات الاحترافية</p>
            </div>
            
            <div class="content">
                <h2>طلب استعادة كلمة المرور</h2>
                <p>مرحباً {user.first_name or 'عزيزي العميل'},</p>
                <p>لقد تلقينا طلباً لاستعادة كلمة المرور الخاصة بحسابك.</p>
                
                <div class="code-box">
                    <p style="margin: 0 0 10px 0; color: #666;">رمز التحقق الخاص بك:</p>
                    <div class="code">{code}</div>
                </div>
                
                <div class="warning">
                    <strong>⚠️ تنبيه:</strong> هذا الرمز صالح لمدة <strong>15 دقيقة</strong> فقط.
                </div>
                
                <p>إذا لم تطلب استعادة كلمة المرور، يرجى تجاهل هذه الرسالة.</p>
            </div>
            
            <div class="footer">
                <p>© 2024 متجر الأدوات الكهربائية - جميع الحقوق محفوظة</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text message
    plain_message = f"""
    مرحباً {user.first_name or 'عزيزي العميل'},
    
    لقد تلقينا طلباً لاستعادة كلمة المرور الخاصة بحسابك.
    
    رمز التحقق الخاص بك: {code}
    
    هذا الرمز صالح لمدة 15 دقيقة فقط.
    
    إذا لم تطلب استعادة كلمة المرور، يرجى تجاهل هذه الرسالة.
    
    متجر الوسام للأدوات الكهربائية
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """
    إرسال رسالة ترحيب للمستخدم الجديد
    """
    subject = 'مرحباً بك في متجر الوسام للأدوات الكهربائية! 🎉'
    
    # Create HTML message
    html_message = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Cairo', 'Segoe UI', Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
                direction: rtl;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
                color: #ffffff;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 32px;
                font-weight: 900;
            }}
            .highlight {{
                color: #FFD700;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .welcome-message {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .welcome-message h2 {{
                color: #000000;
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .features {{
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
            .feature-item {{
                padding: 15px;
                border-right: 4px solid #FFD700;
                margin-bottom: 15px;
                background-color: #ffffff;
                border-radius: 5px;
            }}
            .feature-item h3 {{
                color: #000000;
                margin: 0 0 5px 0;
                font-size: 18px;
            }}
            .feature-item p {{
                margin: 0;
                color: #666;
                font-size: 14px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FFD700;
                color: #000000;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 900;
                font-size: 18px;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 20px;
                text-align: center;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ الأدوات <span class="highlight">الكهربائية</span></h1>
                <p>متجرك الموثوق للأدوات الاحترافية</p>
            </div>
            
            <div class="content">
                <div class="welcome-message">
                    <h2>🎉 مرحباً بك {user.first_name or 'عزيزي العميل'}!</h2>
                    <p>نحن سعداء بانضمامك إلى عائلة الوسام متجر الأدوات الكهربائية</p>
                </div>
                
                <div class="features">
                    <div class="feature-item">
                        <h3>🛠️ منتجات عالية الجودة</h3>
                        <p>نوفر لك أفضل الأدوات الكهربائية من علامات تجارية موثوقة</p>
                    </div>
                    
                    <div class="feature-item">
                        <h3>🚚 توصيل سريع</h3>
                        <p>نضمن وصول طلباتك في الوقت المحدد وبأمان تام</p>
                    </div>
                    
                    <div class="feature-item">
                        <h3>💰 أسعار تنافسية</h3>
                        <p>عروض وخصومات حصرية على مدار العام</p>
                    </div>
                    
                    <div class="feature-item">
                        <h3>📞 دعم فني متميز</h3>
                        <p>فريقنا جاهز لمساعدتك في أي وقت</p>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <p><strong>ابدأ تسوقك الآن واستمتع بتجربة مميزة!</strong></p>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2024 متجر الوسام الأدوات الكهربائية - جميع الحقوق محفوظة</p>
                <p>تم إنشاء حسابك بنجاح باستخدام البريد الإلكتروني: {user.email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text message
    plain_message = f"""
    مرحباً بك {user.first_name or 'عزيزي العميل'}!
    
    نحن سعداء بانضمامك إلى عائلةالوسام متجر الأدوات الكهربائية.
    
    ما الذي يميزنا:
    
    🛠️ منتجات عالية الجودة من علامات تجارية موثوقة
    🚚 توصيل سريع وآمن
    💰 أسعار تنافسية وعروض حصرية
    📞 دعم فني متميز
    
    ابدأ تسوقك الآن واستمتع بتجربة مميزة!
    
    تم إنشاء حسابك بنجاح باستخدام البريد الإلكتروني: {user.email}
    
    متجر الأدوات الكهربائية
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
