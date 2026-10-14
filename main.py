"""Run from a source checkout without requiring an editable installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from auravlian.app.bootstrap import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

