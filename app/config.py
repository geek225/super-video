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

PROVIDER_PRESETS = {
    "default": "",
    "google_veo": "https://generativelanguage.googleapis.com/v1beta",
    "openai_sora": "https://api.openai.com/v1",
    "kling_ai": "https://api.klingai.com/v1",
    "higgsfield": "https://api.higgsfield.ai/v1",
    "fal_ai": "https://queue.fal.run",
}


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


def get_provider_mode() -> str:
    """Récupère l'identifiant du moteur sélectionné (default, google_veo, openai_sora, kling_ai, higgsfield, fal_ai, custom)."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    mode = os.getenv("STUDIO_PROVIDER_MODE", "").strip()
    if mode:
        return mode
    base = get_base_url()
    if base == get_default_base_url():
        return "default"
    for k, url in PROVIDER_PRESETS.items():
        if url and base.startswith(url):
            return k
    return "custom"


def save_provider_mode(mode: str) -> None:
    clean_mode = mode.strip() or "default"
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    set_key(str(ENV_PATH), "STUDIO_PROVIDER_MODE", clean_mode)
    os.environ["STUDIO_PROVIDER_MODE"] = clean_mode


def get_custom_model() -> str:
    """Récupère le nom du modèle personnalisé éventuel (ex: veo-3.0-generate-preview, sora-2, kling-v2, etc.)."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("STUDIO_CUSTOM_MODEL", "").strip()


def save_custom_model(model_name: str) -> None:
    clean_model = model_name.strip()
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    set_key(str(ENV_PATH), "STUDIO_CUSTOM_MODEL", clean_model)
    os.environ["STUDIO_CUSTOM_MODEL"] = clean_model


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


def reset_to_free_pool() -> None:
    """Réinitialise la configuration pour revenir au Pool Gratuit Super Video AI (5 clés en rotation)."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    legacy_key_env, legacy_url_env = get_legacy_env_names()
    for var in ("STUDIO_API_KEY", "STUDIO_BASE_URL", "STUDIO_PROVIDER_MODE", "STUDIO_CUSTOM_MODEL", legacy_key_env, legacy_url_env):
        set_key(str(ENV_PATH), var, "")
        os.environ[var] = ""
