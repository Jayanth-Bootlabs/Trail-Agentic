from pathlib import Path
import sys


# Make the backend's top-level packages (graph, nodes, utils, etc.) importable
# whether pytest is launched from this folder or from the repository root.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
