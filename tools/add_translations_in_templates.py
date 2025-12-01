"""
Script to (safely) add Django translation tags to template files.
- Adds `{% load i18n %}` if missing.
- Wraps visible static strings in `{% trans %}` or `{% blocktrans %}`.
- Translates HTML attributes commonly displayed to users (alt, title, placeholder, aria-label).

Limitations:
- This is heuristic-based — review output, especially for JS/embedded content.
- Does not handle strings with template variables inside simple `trans`; it uses `blocktrans` when variables are present.
- Always creates a `.bak` backup for each edited file.

Usage:
python tools/add_translations_in_templates.py

"""
import re
from bs4 import BeautifulSoup, NavigableString, Comment
import os
import io

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # project root
TEMPLATE_DIRS = []

# Walk to find template html files
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    # skip migrations / static / media
    if any(x in dirpath.split(os.sep) for x in ['migrations', 'static', 'media', 'node_modules']):
        continue
    for f in filenames:
        if f.endswith('.html'):
            TEMPLATE_DIRS.append(os.path.join(dirpath, f))

# Utility: check if string contains arabic letters: use Unicode range
ARABIC_RE = re.compile('[\u0600-\u06FF]')
# NOTE: Using only Arabic and Latin checks via explicit range or A-Za-z

# Tag names to skip
SKIP_TAGS = set(['script', 'style', 'pre', 'code', 'textarea'])

# Attributes to translate
ATTRS_TO_TRANSLATE = ['alt', 'title', 'placeholder', 'aria-label', 'value', 'label']

# Pattern to detect template tags inside string
TEMPLATE_PAT = re.compile(r'(\{\{|\{%|%\}|}})')


def must_translate_text(s: str) -> bool:
    if not s:
        return False
    raw = s.strip()
    if not raw:
        return False
    # skip if contains template tags
    if TEMPLATE_PAT.search(raw):
        return False
    # skip if it's a single punctuation or number only
    if re.fullmatch(r'[\d\W_]+', raw):
        return False
    # check for Arabic characters (or other letters)
    if re.search('[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', raw) or re.search('[A-Za-z]', raw):
        return True
    return False


def to_trans_literal(s: str) -> str:
    # escape double quotes and newlines
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    return s


def process_template(path: str):
    # Read using utf-8 with fallback to cp1256 if needed
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        with io.open(path, 'r', encoding='cp1256', errors='replace') as f:
            content = f.read()

    original = content
    modified = False

    # Add load i18n if not present
    if '{% load i18n %}' not in content:
        # attempt to insert after first load static or at top
        if '{% load static %}' in content:
            content = content.replace('{% load static %}', '{% load static %}\n{% load i18n %}', 1)
            modified = True
        else:
            # place it after DOCTYPE or at top
            if re.search(r'<!DOCTYPE|<html', content, re.I):
                content = '{% load i18n %}\n' + content
                modified = True

    soup = BeautifulSoup(content, 'html.parser')

    # Translate attributes
    for tag in soup.find_all(True):
        if tag.name.lower() in SKIP_TAGS:
            continue
        for attr in ATTRS_TO_TRANSLATE:
            if attr in tag.attrs:
                val = tag[attr]
                if isinstance(val, list):
                    val = ' '.join(val)
                # skip if value contains variables or trans already
                if TEMPLATE_PAT.search(val):
                    continue
                if '{{' in val or '{%' in val:
                    continue
                if must_translate_text(val):
                    new_val = '{% trans \"' + to_trans_literal(val) + '\" %}'
                    tag[attr] = new_val
                    modified = True

    # Translate Text Nodes
    for element in soup.find_all(text=True):
        if isinstance(element, Comment):
            continue
        parent = element.parent
        if parent and parent.name and parent.name.lower() in SKIP_TAGS:
            continue
        text = str(element)
        if must_translate_text(text):
            # If parent contains more than only this text, create blocktrans
            sibling_texts = ''.join([str(x) for x in parent.contents if isinstance(x, NavigableString)])
            if len(parent.contents) == 1 and isinstance(parent.contents[0], NavigableString):
                # simple single text node; use trans
                new = parent.string.replace(text, '{% trans "' + to_trans_literal(text.strip()) + '" %}')
                parent.string.replace_with('{% trans "' + to_trans_literal(text.strip()) + '" %}')
                modified = True
            else:
                # Mixed content or variables; use blocktrans
                # Identify variables inside text
                vars_in_text = re.findall(r'\{\{\s*([^}]+)\s*\}\}', text)
                if vars_in_text:
                    # blocktrans should reference variables without braces
                    # Example: {% blocktrans %}Price: {{ price }}{% endblocktrans %}
                    # We'll assemble a blocktrans string to replace the text node
                    block_content = text
                    new_block = '{% blocktrans %}' + block_content + '{% endblocktrans %}'
                    element.replace_with(new_block)
                    modified = True
                else:
                    # just plain text embedded with other content; replace with trans tag
                    new_text = '{% trans "' + to_trans_literal(text.strip()) + '" %}'
                    element.replace_with(new_text)
                    modified = True

    if modified:
        # Write backup
        backup_path = path + '.bak'
        if not os.path.exists(backup_path):
            with io.open(backup_path, 'w', encoding='utf-8') as b:
                b.write(original)

        # Save changes
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print('Updated:', path)
    else:
        print('No change:', path)


if __name__ == '__main__':
    print('Scanning templates ...')
    for t in TEMPLATE_DIRS:
        process_template(t)
    print('Done.')
