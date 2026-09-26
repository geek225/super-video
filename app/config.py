import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Chemins racines du projet
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Création des dossiers nécessaires s'ils n'existent pas
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Chargement du fichier .env
load_dotenv(dotenv_path=ENV_PATH)

def get_api_key() -> str:
    """Récupère la clé API Agnes AI."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("AGNES_API_KEY", "").strip()

def save_api_key(key: str) -> None:
    """Met à jour la clé API Agnes AI dans le fichier .env."""
    clean_key = key.strip()
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    set_key(str(ENV_PATH), "AGNES_API_KEY", clean_key)
    os.environ["AGNES_API_KEY"] = clean_key

def get_base_url() -> str:
    """Récupère l'URL de base pour l'API Agnes AI ou un fournisseur alternatif."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").strip()

def save_base_url(url: str) -> None:
    """Met à jour l'URL de base de l'API dans le fichier .env."""
    clean_url = url.strip()
    if not clean_url:
        clean_url = "https://apihub.agnes-ai.com/v1"
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    set_key(str(ENV_PATH), "AGNES_BASE_URL", clean_url)
    os.environ["AGNES_BASE_URL"] = clean_url
