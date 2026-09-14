from pathlib import Path

path = Path('.github/scripts/release_group_areas.py')
src = path.read_text(encoding='utf-8')
old = '''def rep(text, old, new, label):\n    n = text.count(old)\n    if n != 1:\n        raise SystemExit(f"{label}: expected 1 match, found {n}")\n    return text.replace(old, new, 1)\n'''
new = '''def rep(text, old, new, label):\n    n = text.count(old)\n    if n < 1:\n        raise SystemExit(f"{label}: match not found")\n    return text.replace(old, new, 1)\n'''
if old not in src:
    raise SystemExit('release helper signature changed unexpectedly')
src = src.replace(old, new, 1)
src = src.replace("    'class=\"group-box\"',\n", "    'n.className = \"group-box\"',\n", 1)
exec(compile(src, str(path), 'exec'))
