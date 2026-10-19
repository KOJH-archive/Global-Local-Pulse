from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = yaml.safe_load((ROOT / 'config/countries.yaml').read_text())
SETTINGS = yaml.safe_load((ROOT / 'config/scoring.yaml').read_text())
