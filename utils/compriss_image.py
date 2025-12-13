import os
import uuid
from PIL import Image

def convert_to_webp_and_delete_original(image_field, quality=85, max_size=(1200, 1200)):
    """يحفظ نسخة WebP مضغوطة باسم فريد ثم يحذف الأصلية"""

    if not image_field:
        return

    old_path = image_field.path
    dir_path, ext = os.path.splitext(old_path)

    # لو الصورة أصلاً webp لا نعيد المعالجة
    if ext.lower() == ".webp":
        return

    # إنشاء معرف فريد لتجنب استبدال الصور
    unique_id = uuid.uuid4().hex
    new_path = f"{dir_path}_{unique_id}.webp"

    # فتح الصورة وتصغيرها
    img = Image.open(old_path)
    img.thumbnail(max_size, Image.LANCZOS)

    # تحويل الصورة إلى RGB أو RGBA
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # حفظ الصورة الجديدة بصيغة WebP
    img.save(new_path, "WEBP", quality=quality, optimize=True)

    # حذف الصورة الأصلية
    if os.path.exists(old_path):
        os.remove(old_path)

    # تحديث الحقل للإشارة للصورة الجديدة
    image_field.name = image_field.name.rsplit('.', 1)[0] + f"_{unique_id}.webp"
