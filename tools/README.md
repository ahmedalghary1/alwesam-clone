# Translation Automation Tools

This folder contains a script to help automate adding Django translation tags to templates.

Files:
- `add_translations_in_templates.py` — Heuristically scans templates and adds `{% load i18n %}`, wraps plain texts in `{% trans %}` or `{% blocktrans %}` where variables are detected.

Usage:
1. Install dependencies (preferably inside a virtualenv):

```powershell
pip install -r requirements.txt
```

2. Run the script (it will back up each modified file as `<file>.bak`):

```powershell
python tools/add_translations_in_templates.py
```

3. Review changes carefully. The script is heuristic-based and may require manual review, especially for text inside JS, CSS, or complex HTML.

4. Once templates have `trans` tags, extract `.po` files with Django `makemessages` (ensure gettext utilities are installed on your system and `python` points to your project environment):

```powershell
python manage.py makemessages -l ar
# Check the generated PO files in the `locale/ar/LC_MESSAGES` folder
# Edit `django.po` to add translations if needed
python manage.py compilemessages
```

Notes:
- On Windows, you need to install gettext and ensure `xgettext`/`msgfmt` are on PATH. See: https://mlocati.github.io/articles/gettext-iconv-windows.html
- The script only targets `.html` templates under `templates/` and app-specific templates. It skips `script` and `style` tags to avoid injecting Django tags into JS/CSS.
- Some cases cannot be auto-wrapped safely (e.g., strings containing template variables). The script uses `blocktrans` where it detects `{{ var }}`, but manual review is recommended.

If you want me to run the script and/or generate `.po` files in this environment, tell me and I will run the steps (I may need to install packages and/or gettext utilities on your machine).
