import base64
import datetime
import hashlib
import hmac
import json
import os
import random
import re
import sys
import zlib
from pathlib import Path
from typing import List, Optional, Tuple, Dict

_VAULT_SALT = b"SVA_KevinoGeek_2026_Studio_Vault_Key!"

# URLs et identifiants moteur chiffrés (Zéro mention du fournisseur en clair)
_SEALED_BASE_URL = "D~yVFVoYA&ytoKSt*3W?;(2<I7+Iq!rMncEuAoClTT9MlE9d"
_SEALED_QUERY_URL = "D~yVFVoYA&ytoKSt*3W?;(2<I7+Iq!rMncEuAplN-&tjhH(m+"
_SEALED_DEFAULT_MODEL = "D~t*ggf3gZL!=8VsJv?61Lu2`8d$qzX+6PFF#"
_SEALED_LEGACY_MODEL = "D~t*ggf3gZL!=8VsJwCk;sG{aU@~yx"
_SEALED_ENV_KEY = "D~vKLycT=s8DqEUk{!}EFet}dqW"
_SEALED_ENV_URL = "D~vKLycT=s868U#=wwpBF)}EpS5E"

# Pool de clés partagées chiffrées (Solution C : Rotation automatique & Failover)
_SEALED_KEY_POOL: List[str] = [
    "D~xK9oe+7Tn4hss&6!dBI3N0HV0d^*Uqve=7yq1sP`?&bQW_yL62g&yVj^5}s7e@>9x*bFOG0%",
    "D~xK9ohba7o+q<YOJ4EDy21icV|=?yLt|A~Z`qtXl0p`B=v^I1k%89UMIE8ctuCBt`ZF^2TSC_",
    "D~xK9ov3+Z86&VSu0*KEe?A#iT|vHYL>_YIRk@gc6@ke$F4`UqafMZY<)U6pO)EffL@_esh(TQ",
    "D~xK9oe=${q2M*DR6tZheL$b9W4w4OrXN+AseYxosAnq=6MrL3P+`<wrkf;;R};jO0yHxD-a@k",
    "D~xK9ok)bDre`!rOvIOjd>H|%dI3RKCSh0mtw5#)QbBJsEZN)(lmtmV#$>~dNs(nO`!O=@uR#O",
]

# Mémorisation en mémoire de la clé ayant créé chaque video_id pour le suivi SSE
_TASK_KEY_MAP: Dict[str, str] = {}

DAILY_SHARED_LIMIT = 5


def seal_secret(plain_text: str) -> str:
    """Chiffre une chaîne sensible (Zlib + XOR + Base85) pour le coffre-fort."""
    comp = zlib.compress(plain_text.encode("utf-8"), level=9)
    xored = bytes(b ^ _VAULT_SALT[i % len(_VAULT_SALT)] for i, b in enumerate(comp))
    return base64.b85encode(xored).decode("ascii")


def unseal_secret(sealed_blob: str) -> str:
    """Déchiffre en mémoire une chaîne issue du coffre-fort."""
    raw = base64.b85decode(sealed_blob.encode("ascii"))
    unxored = bytes(b ^ _VAULT_SALT[i % len(_VAULT_SALT)] for i, b in enumerate(raw))
    return zlib.decompress(unxored).decode("utf-8")


def get_default_base_url() -> str:
    return unseal_secret(_SEALED_BASE_URL)


def get_default_query_url() -> str:
    return unseal_secret(_SEALED_QUERY_URL)


def get_default_model_id() -> str:
    return unseal_secret(_SEALED_DEFAULT_MODEL)


def get_legacy_model_id() -> str:
    return unseal_secret(_SEALED_LEGACY_MODEL)


def sanitize_provider_text(text: str) -> str:
    """Masque toute mention interne du fournisseur dans les messages d'erreur renvoyés au client."""
    if not text:
        return ""
    p = unseal_secret(_SEALED_ENV_KEY)[:5].lower()
    cleaned = re.sub(rf"(?i){p}-video-[a-z0-9.\-]+", "Super Video Engine", str(text))
    cleaned = re.sub(rf"(?i){p}(-ai|ai)?", "Super Video AI", cleaned)
    return cleaned


def get_legacy_env_names() -> Tuple[str, str]:
    return unseal_secret(_SEALED_ENV_KEY), unseal_secret(_SEALED_ENV_URL)


def get_shared_pool_keys() -> List[str]:
    keys: List[str] = []
    for blob in _SEALED_KEY_POOL:
        try:
            k = unseal_secret(blob).strip()
            if k and k not in keys:
                keys.append(k)
        except Exception:
            continue

    extra_pool = os.getenv("STUDIO_KEY_POOL", "").strip()
    if extra_pool:
        for item in extra_pool.split(","):
            val = item.strip()
            if not val:
                continue
            try:
                if val.startswith("D~"):
                    val = unseal_secret(val).strip()
            except Exception:
                pass
            if val and val not in keys:
                keys.append(val)

    random.shuffle(keys)
    return keys


def resolve_candidate_keys(user_configured_key: Optional[str] = None) -> Tuple[List[str], bool]:
    """
    Retourne (liste_de_cles, utilise_pool_partage).
    - Si l'utilisateur a configuré sa propre clé (ou une liste séparée par des virgules) :
      Mode Personnel Illimité (utilise_pool_partage = False).
    - Sinon : bascule sur le Pool de clés partagées en rotation aléatoire (utilise_pool_partage = True).
    """
    pool_keys = get_shared_pool_keys()
    if user_configured_key and user_configured_key.strip():
        custom_list = [k.strip() for k in user_configured_key.split(",") if k.strip()]
        non_pool_keys = [k for k in custom_list if k not in pool_keys]
        if non_pool_keys:
            random.shuffle(non_pool_keys)
            return non_pool_keys + pool_keys, False
        if custom_list:
            random.shuffle(custom_list)
            return custom_list, True

    return pool_keys, True


def register_task_key(video_id: str, api_key: str) -> None:
    if video_id and api_key:
        _TASK_KEY_MAP[video_id] = api_key


def get_task_key(video_id: str) -> Optional[str]:
    return _TASK_KEY_MAP.get(video_id)


def _quota_file_path(base_dir: Path) -> Path:
    return base_dir / ".quota.dat"


def _sign_quota(date_str: str, count: int) -> str:
    msg = f"{date_str}:{count}".encode("utf-8")
    return hmac.new(_VAULT_SALT, msg, hashlib.sha256).hexdigest()


def get_shared_quota_status(base_dir: Path) -> Tuple[int, int]:
    """Retourne (utilisé_aujourd_hui, limite_journalière)."""
    qfile = _quota_file_path(base_dir)
    today = datetime.date.today().isoformat()
    if not qfile.exists():
        return 0, DAILY_SHARED_LIMIT
    try:
        raw = base64.b85decode(qfile.read_bytes()).decode("utf-8")
        data = json.loads(raw)
        d_str = data.get("d", "")
        cnt = int(data.get("c", 0))
        sig = data.get("s", "")
        if d_str != today:
            return 0, DAILY_SHARED_LIMIT
        if not hmac.compare_digest(sig, _sign_quota(d_str, cnt)):
            return DAILY_SHARED_LIMIT, DAILY_SHARED_LIMIT
        return cnt, DAILY_SHARED_LIMIT
    except Exception:
        return 0, DAILY_SHARED_LIMIT


def consume_shared_quota(base_dir: Path) -> None:
    """Incrémente le compteur journalier du Pool partagé avec signature HMAC anti-triche."""
    used, _ = get_shared_quota_status(base_dir)
    today = datetime.date.today().isoformat()
    new_count = used + 1
    payload = {
        "d": today,
        "c": new_count,
        "s": _sign_quota(today, new_count),
    }
    encoded = base64.b85encode(json.dumps(payload).encode("utf-8"))
    try:
        _quota_file_path(base_dir).write_bytes(encoded)
    except Exception:
        pass


def add_keys_to_vault_file(plain_keys: List[str]) -> int:
    """Utilitaire CLI permettant au créateur d'ajouter facilement de nouvelles clés chiffrées au Pool."""
    existing_plain = set()
    for blob in _SEALED_KEY_POOL:
        try:
            existing_plain.add(unseal_secret(blob).strip())
        except Exception:
            pass

    new_blobs = list(_SEALED_KEY_POOL)
    added = 0
    for k in plain_keys:
        clean = k.strip()
        if clean and clean not in existing_plain:
            new_blobs.append(seal_secret(clean))
            existing_plain.add(clean)
            added += 1

    if added > 0:
        this_file = Path(__file__).resolve()
        content = this_file.read_text(encoding="utf-8")
        items_str = "\n".join(f'    "{b}",' for b in new_blobs)
        new_block = f"_SEALED_KEY_POOL: List[str] = [\n{items_str}\n]"
        updated = re.sub(
            r"_SEALED_KEY_POOL:\s*List\[str\]\s*=\s*\[[^\]]*\]",
            lambda _: new_block,
            content,
            count=1,
        )
        this_file.write_text(updated, encoding="utf-8")
    return added


if __name__ == "__main__":
    if len(sys.argv) > 1:
        count = add_keys_to_vault_file(sys.argv[1:])
        print(f"✓ {count} nouvelle(s) clé(s) chiffrée(s) et ajoutée(s) au Pool Super Video AI.")
    else:
        print(f"Pool actuel : {len(get_shared_pool_keys())} clé(s) active(s) chiffrée(s).")
        print("Usage pour ajouter des clés : python3 -m app.security_vault CLE_1 CLE_2 ...")
