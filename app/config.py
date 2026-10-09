import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from app.security_vault import (
    get_default_base_url,
    get_legacy_env_names,
    resolve_candidate_keys,
)

# Chemin racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# S'assurer que les dossiers existent
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Charger les variables d'environnement depuis .env s'il existe
load_dotenv(dotenv_path=ENV_PATH, override=True)


def get_user_api_key() -> str:
    """Récupère uniquement la clé configurée localement par l'utilisateur dans .env."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    legacy_key_env, _ = get_legacy_env_names()
    return (
        os.getenv("STUDIO_API_KEY", "").strip()
        or os.getenv(legacy_key_env, "").strip()
    )


def get_api_key() -> str:
    """
    Récupère une clé active :
    - Soit la clé personnelle de l'utilisateur
    - Soit une clé issue du Pool chiffré en rotation (Solution C).
    """
    user_key = get_user_api_key()
    candidates, _ = resolve_candidate_keys(user_key)
    return candidates[0] if candidates else ""


def save_api_key(api_key: str) -> None:
    """Enregistre la clé Studio de manière sécurisée dans le fichier .env local."""
    clean_key = api_key.strip()
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    set_key(str(ENV_PATH), "STUDIO_API_KEY", clean_key)
    os.environ["STUDIO_API_KEY"] = clean_key


def get_base_url() -> str:
    """Récupère l'URL de base de l'API depuis .env ou le coffre-fort chiffré."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    _, legacy_url_env = get_legacy_env_names()
    val = (
        os.getenv("STUDIO_BASE_URL", "").strip()
        or os.getenv(legacy_url_env, "").strip()
    )
    if not val or val == "default":
        return get_default_base_url()
    return val.rstrip("/")


def save_base_url(base_url: str) -> None:
    """Enregistre l'URL de base du fournisseur dans .env."""
    clean_url = base_url.strip().rstrip("/")
    if clean_url == "default" or clean_url == get_default_base_url():
        clean_url = ""
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    set_key(str(ENV_PATH), "STUDIO_BASE_URL", clean_url)
    os.environ["STUDIO_BASE_URL"] = clean_url
