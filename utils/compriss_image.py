import os
from PIL import Image

def convert_to_webp_and_delete_original(image_field, quality=85, max_size=(1200, 1200)):
    """يحفظ نسخة WebP مضغوطة ثم يحذف الأصلية"""

    if not image_field:
        return

    old_path = image_field.path
    dir_path, ext = os.path.splitext(old_path)

    # لو الصورة أصلاً webp لا نعيد المعالجة
    if ext.lower() == ".webp":
        return

    new_path = dir_path + ".webp"

    img = Image.open(old_path)

    # تصغير
    img.thumbnail(max_size, Image.LANCZOS)

    # تحويل RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # حفظ الجديدة
    img.save(new_path, "WEBP", quality=quality, optimize=True)

    # حذف القديمة
    if os.path.exists(old_path):
        os.remove(old_path)

    # تعديل الحقل للإشارة للصورة الجديدة
    image_field.name = image_field.name.rsplit('.', 1)[0] + ".webp"
