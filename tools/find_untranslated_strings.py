"""
Find and report lines in templates that contain visible Arabic text not wrapped in Django translation tags.

Usage:
python tools/find_untranslated_strings.py

This script prints a list of candidate lines for manual review.
"""
import os
import io
import re
from pathlib import Path

ROOT_DIR = str(Path.cwd())

ARABIC_RE = re.compile('[\u0600-\u06FF]')
TRANS_RE = re.compile(r"\{%\s*(trans|blocktrans)\b")

SKIP_DIRS = {'migrations', 'static', 'media', '__pycache__'}

results = []
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    # skip directories
    parts = set(dirpath.split(os.sep))
    if parts & SKIP_DIRS:
        continue
    for f in filenames:
        if f.endswith('.html'):
            path = os.path.join(dirpath, f)
            with io.open(path, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
            for i, line in enumerate(lines, start=1):
                if ARABIC_RE.search(line):
                    # skip if this file contains 'trans' or this line already has trans
                    if TRANS_RE.search(line):
                        continue
                    # skip lines within style or script tags: naive check
                    if '<script' in line.lower() or '<style' in line.lower():
                        continue
                    # heuristic: skip lines that contain templating expressions only
                    if '{{' in line and '}}' in line and line.strip().startswith('{{'):
                        continue
                    results.append(f'{path}:{i}: {line.strip()}')

out_file = os.path.join('tools', 'untranslated_report.txt')
with io.open(out_file, 'w', encoding='utf-8') as out:
    out.write('\n'.join(results))
print(f'Scan complete. See {out_file} for the report.')
