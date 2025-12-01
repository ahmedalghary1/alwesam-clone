# متجر الأدوات الكهربائية - Django E-Commerce

## 🚀 تشغيل المشروع

### 1. تفعيل البيئة الافتراضية
```bash
source ../bin/activate  # أو: source venv/bin/activate
```

### 2. تطبيق Migrations
```bash
python manage.py migrate
```

### 3. إنشاء مستخدم admin
```bash
python manage.py createsuperuser
```

### 4. إنشاء بيانات تجريبية
```bash
# إنشاء التصنيفات
python manage.py create_sample_categories

# إنشاء رسوم التوصيل
python manage.py create_delivery_fee
```

### 5. تشغيل السيرفر
```bash
python manage.py runserver
```

## 📋 الروابط المهمة

- **الموقع الرئيسي**: http://localhost:8000/
- **المنتجات**: http://localhost:8000/products/
- **تسجيل الدخول**: http://localhost:8000/accounts/login/
- **التسجيل**: http://localhost:8000/accounts/register/
- **السلة**: http://localhost:8000/orders/checkout/
- **طلباتي**: http://localhost:8000/orders/
- **الملف الشخصي**: http://localhost:8000/accounts/profile/
- **لوحة التحكم (Admin Panel)**: http://localhost:8000/admin-panel/
- **Django Admin**: http://localhost:8000/admin/

## ✨ الميزات المكتملة

### ✅ نظام المصادقة
- تسجيل الدخول بالبريد الإلكتروني
- التسجيل
- تسجيل الخروج
- الملف الشخصي

### ✅ نظام المنتجات
- عرض المنتجات
- البحث في المنتجات
- الفلترة حسب (الفئة، السعر، التوفر)
- الترتيب حسب (السعر، الاسم، الأحدث)
- التصنيفات (Categories)

### ✅ نظام الطلبات
- إضافة للسلة
- صفحة Checkout
- إنشاء الطلب (الدفع عند الاستلام)
- عرض طلباتي
- تفاصيل الطلب

### ✅ لوحة التحكم (Admin Panel)
- Dashboard مع إحصائيات
- إدارة المنتجات (إضافة، تعديل، حذف)
- إدارة الطلبات (عرض، تحديث الحالة)
- عرض المستخدمين

## 🎨 الهوية البصرية

- **الألوان الرئيسية**: أسود (#000000) + ذهبي (#FFD700)
- **الخط**: Cairo (عربي)
- **التصميم**: RTL، Bootstrap 5.3

## 📁 هيكل المشروع

```
src/
├── accounts/          # نظام المستخدمين
├── products/          # المنتجات والتصنيفات
├── orders/            # الطلبات والسلة
├── home/              # الصفحة الرئيسية
├── admin_panel/       # لوحة التحكم المخصصة
├── project/           # إعدادات Django
├── static/            # ملفات CSS/JS/Images
└── templates/         # القوالب العامة
```

## 🔐 الصلاحيات

- **مستخدم عادي**: يمكنه التصفح والطلب
- **is_staff**: يمكنه الوصول للوحة التحكم
- **is_superuser**: صلاحيات كاملة

## 💾 قاعدة البيانات

استخدام SQLite (db.sqlite3) كقاعدة بيانات افتراضية.

### النماذج الرئيسية:
- **CustomUser**: المستخدمين (email-based)
- **Category**: تصنيفات المنتجات
- **Product**: المنتجات
- **Order**: الطلبات
- **OrderAddress**: عناوين التوصيل
- **Cart**: السلة

## 🛠️ التقنيات المستخدمة

- Django 5.2.7
- Bootstrap 5.3 RTL
- Font Awesome 6.4
- Google Fonts (Cairo)
- jQuery (للـ AJAX)

## 📝 ملاحظات

- طريقة الدفع: **الدفع عند الاستلام فقط**
- البريد الإلكتروني يُستخدم كـ username
- جميع الصفحات responsive
- تطبيق كامل بدون أي API خارجية للدفع

## 🌐 التدويل وI18N (Internationalization)

- تمت إضافة أدوات للمساعدة في وضع وسوم الترجمة في القوالب تلقائياً تحت المجلد `tools/`.
- سكربت `tools/add_translations_in_templates.py` يقوم بإضافة `{% load i18n %}` ولف النصوص الثابتة بـ `{% trans %}` أو `{% blocktrans %}` إن لزم الأمر. نسخة احتياطية (`.bak`) تُنشأ قبل التعديل.
- سكربت `tools/find_untranslated_strings.py` يولد تقريراً في `tools/untranslated_report.txt` يحدّد الأماكن التي تحتاج مراجعة يدوية.
- لتوليد ملفات .po وملفات .mo المُجمّعة:

```powershell
& "e:/web dev/alwesam/Scripts/python.exe" manage.py makemessages -l ar
& "e:/web dev/alwesam/Scripts/python.exe" manage.py makemessages -l en
& "e:/web dev/alwesam/Scripts/python.exe" manage.py compilemessages
```

- بعد ذلك، راجع `locale/<lang>/LC_MESSAGES/django.po` وأدخل الترجمات المطلوبة ثم شغّل `compilemessages` مجدداً.
- ملاحظة: يجب تثبيت أدوات gettext على النظام (xgettext/msgfmt) ليعمل `makemessages/compilemessages` بشكل صحيح على Windows.
