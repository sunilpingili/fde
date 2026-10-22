import sys
from pathlib import Path

# Add the project root to sys.path so that service.py, database.py, etc.
# are importable when pytest runs from any working directory.
sys.path.insert(0, str(Path(__file__).parent))
