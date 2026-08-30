""" Pytest entry point.
"""

import sys
from pathlib import Path

# Make `import ext...` resolve regardless of where pytest is invoked from -
# insert the directory *containing* the `ext` package (its parent) onto
# sys.path.
_PACKAGE_PARENT = Path(__file__).resolve().parents[2]
if str(_PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_PARENT))

import bpy_stub  # local helper, tests/bpy_stub.py

bpy_stub.foo()
