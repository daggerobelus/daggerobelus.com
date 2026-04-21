import sys
from pathlib import Path

# Add scripts/ to sys.path so tests can import parse_recipes
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
