"""Legacy `python scripts/mapgen_compiler.py` / `python -m mapgen_compiler` entry.

B-2: no sys.path hack. Imports resolve via the installed dist
(py-modules + mapgen package, package-dir scripts/), via
``PYTHONPATH=scripts`` or ``cwd=scripts`` for source runs, or via
pytest ``pythonpath`` for test runs (plain ``python -m`` from repo
root without install still fails — use ``pip install -e .`` there).
"""

from mapgen.cli import main

if __name__ == "__main__":
    main()
