"""Build dist/codex-delegate.zip for upload as a claude.ai account skill."""
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
skill = root / "codex-delegate"
out = root / "dist" / "codex-delegate.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(skill.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            z.write(path, path.relative_to(root).as_posix())
print(out)
