from pathlib import Path

src = Path(".github/scripts/release_group_manual_sizing.py").read_text(encoding="utf-8")
old = 'for token in ("Use manual sizing", "Lock box", "four touch-friendly corner handles"):'
new = 'for token in ("Use manual sizing", "Lock box", "drag any corner handle to resize it"):'
if src.count(old) != 1:
    raise SystemExit("retry patch: expected one README verification tuple")
src = src.replace(old, new, 1)
exec(compile(src, ".github/scripts/release_group_manual_sizing.py", "exec"))
