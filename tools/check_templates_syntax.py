"""
Validate Django template syntax across the project by parsing templates with a Django Engine.
- Prints files that fail to parse (TemplateSyntaxError) with details.
- Optionally attempts to autoload `{% load i18n %}` when `trans` or `blocktrans` are used but i18n was not loaded.

Usage:
python tools/check_templates_syntax.py
"""
import os
import io
import sys
from pathlib import Path

# Setup Django environment for template engine
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Ensure project root on path so Django modules are importable
ROOT_DIR = Path.cwd()
import sys
sys.path.insert(0, str(ROOT_DIR))
try:
    import django
    from django.template import Engine, TemplateSyntaxError
    django.setup()
except Exception as e:
    print('Could not import Django or configure settings:', e)
    sys.exit(1)

# ROOT_DIR defined above
SKIP_DIRS = {'migrations', 'static', 'media', '__pycache__'}

errors = []

engine = Engine.get_default() if Engine.get_default() else Engine()

for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    # skip directories
    if SKIP_DIRS & set(Path(dirpath).parts):
        continue
    for f in filenames:
        if f.endswith('.html'):
            path = Path(dirpath) / f
            try:
                with io.open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                with io.open(path, 'r', encoding='cp1256', errors='replace') as fh:
                    content = fh.read()
            try:
                # Parse via Engine from_string
                engine.from_string(content)
            except TemplateSyntaxError as ex:
                errors.append((str(path), ex))

if errors:
    report_file = Path('tools/template_syntax_report.txt')
    with io.open(report_file, 'w', encoding='utf-8') as out:
        for p, e in errors:
            out.write(f'{p}: {e}\n')
    print('Template syntax errors found:', len(errors))
    print('Report generated at:', report_file)
else:
    print('No template syntax errors detected.')

# Extra check: files using trans without 'load i18n'
trans_missing = []
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    if SKIP_DIRS & set(Path(dirpath).parts):
        continue
    for f in filenames:
        if f.endswith('.html'):
            path = Path(dirpath) / f
            try:
                with io.open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                with io.open(path, 'r', encoding='cp1256', errors='replace') as fh:
                    content = fh.read()
            has_trans = '{% trans' in content or '{% blocktrans' in content
            has_load_i18n = '{% load i18n %}' in content
            if has_trans and not has_load_i18n:
                trans_missing.append(str(path))

if trans_missing:
    with io.open('tools/trans_missing_report.txt', 'w', encoding='utf-8') as out:
        out.write('\n'.join(trans_missing))
    print('Files using trans but missing "{% load i18n %}":', len(trans_missing))
    print('Report created at tools/trans_missing_report.txt')
else:
    print('No missing load i18n issues detected.')
