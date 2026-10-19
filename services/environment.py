"""Load the project's .env regardless of the caller's working directory."""
from pathlib import Path
from dotenv import load_dotenv

def load_environment(root=None):
    project_root=Path(root) if root else Path(__file__).resolve().parents[1]
    # Explicit process/server environment always takes precedence over the file.
    load_dotenv(project_root/'.env',override=False)
