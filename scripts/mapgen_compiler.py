import sys
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from mapgen.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
