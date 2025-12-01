"""
Format Django templates for readability while preserving Django template tags and JS/CSS blocks.

Usage:
    python tools/format_templates_html.py

This script will:
- Replace {% ... %}, {{ ... }}, {# ... #} temporarily with placeholders
- Replace <script> and <style> content with placeholders to avoid modifying JS/CSS
- Use BeautifulSoup to prettify the HTML
- Restore placeholders and write back files with '.bak' backups
"""
from pathlib import Path
import re
import io
from bs4 import BeautifulSoup


def _placeholderize(content):
    mapping = {
        'template_tags': {},
        'expressions': {},
        'comments': {},
        'script_blocks': {},
        'style_blocks': {}
    }

    # Replace script blocks first
    def _repl_script(m):
        key = f"__SCRIPT_{len(mapping['script_blocks'])}__"
        mapping['script_blocks'][key] = m.group(0)
        return key

    content = re.sub(r"(?is)<script.*?>.*?</script>", _repl_script, content)

    # Replace style blocks
    def _repl_style(m):
        key = f"__STYLE_{len(mapping['style_blocks'])}__"
        mapping['style_blocks'][key] = m.group(0)
        return key

    content = re.sub(r"(?is)<style.*?>.*?</style>", _repl_style, content)

    # Replace template tags {% ... %}
    def _repl_tag(m):
        key = f"__TAG_{len(mapping['template_tags'])}__"
        mapping['template_tags'][key] = m.group(0)
        return key

    content = re.sub(r"{%.+?%}", _repl_tag, content, flags=re.DOTALL)

    # Replace expressions {{ ... }}
    def _repl_expr(m):
        key = f"__EXPR_{len(mapping['expressions'])}__"
        mapping['expressions'][key] = m.group(0)
        return key

    content = re.sub(r"{{.+?}}", _repl_expr, content, flags=re.DOTALL)

    # Replace comments {# ... #}
    def _repl_comment(m):
        key = f"__CMT_{len(mapping['comments'])}__"
        mapping['comments'][key] = m.group(0)
        return key

    content = re.sub(r"{#.+?#}", _repl_comment, content, flags=re.DOTALL)

    return content, mapping


def _restore_placeholders(content, mapping):
    # Restore comments first (less likely to conflict)
    for key, val in mapping['comments'].items():
        content = content.replace(key, val)

    for key, val in mapping['expressions'].items():
        content = content.replace(key, val)

    for key, val in mapping['template_tags'].items():
        content = content.replace(key, val)

    for key, val in mapping['script_blocks'].items():
        content = content.replace(key, val)

    for key, val in mapping['style_blocks'].items():
        content = content.replace(key, val)

    return content


def format_template_file(path: Path):
    try:
        raw = path.read_text(encoding='utf-8')
    except Exception:
        raw = path.read_text(encoding='cp1256', errors='replace')

    placeholdered, mapping = _placeholderize(raw)

    # Use BeautifulSoup to pretty-print the HTML
    soup = BeautifulSoup(placeholdered, 'html.parser')
    pretty = soup.prettify()

    # Restore placeholders
    restored = _restore_placeholders(pretty, mapping)

    # Normalize excessive blank lines
    restored = re.sub(r"\n\s*\n\s*\n+", '\n\n', restored)

    if restored.strip() == raw.strip():
        return False  # no change

    # Backup and write
    bak = path.with_suffix(path.suffix + '.bak')
    bak.write_text(raw, encoding='utf-8')
    path.write_text(restored, encoding='utf-8')
    return True


def format_all_templates(root_dir: Path):
    modified = []
    for p in root_dir.rglob('*.html'):
        # Skip migrations and static
        if 'migrations' in p.parts or 'static' in p.parts or 'media' in p.parts:
            continue
        changed = format_template_file(p)
        if changed:
            modified.append(str(p))
    return modified


if __name__ == '__main__':
    root = Path.cwd()
    print('Formatting templates under', root)
    modified = format_all_templates(root)
    print('Modified files:', len(modified))
    for m in modified:
        print(' -', m)