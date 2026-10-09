import os
import uuid
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import UPLOADS_DIR

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB max selon les spécifications Super Video AI

class ImageBridgeError(Exception):
    pass

def validate_image_file(filename: str, file_size: int) -> str:
    """Valide l'extension et la taille de l'image."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageBridgeError(f"Extension non supportée: {ext}. Formats acceptés : PNG, JPG, JPEG, WEBP.")
    
    if file_size > MAX_FILE_SIZE:
        raise ImageBridgeError("L'image dépasse la taille maximale autorisée de 15 Mo.")
    
    return ext

def save_local_image(file_bytes: bytes, original_filename: str) -> Path:
    """Sauvegarde l'image uploadée dans le dossier local uploads/."""
    ext = validate_image_file(original_filename, len(file_bytes))
    unique_name = f"{uuid.uuid4().hex[:12]}_{Path(original_filename).name}"
    # Nettoyage du nom de fichier pour éviter toute injection dans le chemin
    clean_name = "".join(c for c in unique_name if c.isalnum() or c in "._-")
    destination = UPLOADS_DIR / clean_name
    
    with open(destination, "wb") as f:
        f.write(file_bytes)
        
    return destination

from PIL import Image

def get_image_dimensions_and_optimal_preset(file_path: Path) -> Dict[str, Any]:
    """
    Analyse les dimensions réelles de l'image avec Pillow et détermine
    le cadrage Super Video AI optimal pour éviter toute coupure de têtes, visages ou trophées.
    """
    try:
        with Image.open(file_path) as im:
            width, height = im.size
            ratio = width / height if height > 0 else 1.0
            
            # Détermination du preset officiel Super Video AI le plus fidèle sans rognage violent
            if ratio >= 1.60:
                preset = "16:9"
                preset_w, preset_h = 1280, 704
                label = f"16:9 Paysage ({width}×{height})"
            elif ratio >= 1.20:
                preset = "4:3"
                preset_w, preset_h = 1088, 832
                label = f"4:3 Paysage standard ({width}×{height})"
            elif ratio >= 0.85:
                preset = "1:1"
                preset_w, preset_h = 960, 960
                label = f"1:1 Carré fidèle ({width}×{height})"
            elif ratio >= 0.60:
                preset = "3:4"
                preset_w, preset_h = 832, 1088
                label = f"3:4 Portrait affiche ({width}×{height})"
            else:
                preset = "9:16"
                preset_w, preset_h = 704, 1280
                label = f"9:16 Story vertical ({width}×{height})"
                
            return {
                "width": width,
                "height": height,
                "aspect_ratio": round(ratio, 3),
                "recommended_ratio": preset,
                "recommended_width": preset_w,
                "recommended_height": preset_h,
                "ratio_label": label
            }
    except Exception as e:
        return {
            "width": 1024,
            "height": 1024,
            "aspect_ratio": 1.0,
            "recommended_ratio": "1:1",
            "recommended_width": 960,
            "recommended_height": 960,
            "ratio_label": "Format Standard (1:1)"
        }

def upload_to_public_host(file_path: Path) -> str:
    """
    Héberge automatiquement et de façon fiable l'image locale sur un CDN public
    afin que les serveurs de rendu d'IA puissent télécharger l'image sans blocage ni coupure réseau.
    Architecture multi-niveaux à tolérance de panne :
    1. CDN FreeImage (iili.io) : haute disponibilité et liens directs sans WAF bloquant
    2. CDN Uguu : relai rapide direct
    3. Litterbox / Catbox : repli supplémentaire
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 1. Tentative Tier 1 : FreeImage CDN (iili.io direct image)
    try:
        with open(file_path, "rb") as f:
            data = {
                "key": "6d207e02198a847aa98d0a2a901485a5",
                "action": "upload",
                "format": "json"
            }
            files = {"source": (file_path.name, f)}
            resp = requests.post("https://freeimage.host/api/1/upload", data=data, files=files, headers=headers, timeout=20)
            if resp.status_code == 200:
                res_json = resp.json()
                img_url = res_json.get("image", {}).get("url")
                if img_url and img_url.startswith("http"):
                    return img_url
    except Exception:
        pass

    # 2. Tentative Tier 2 : Uguu CDN
    try:
        with open(file_path, "rb") as f:
            files = {"files[]": (file_path.name, f)}
            resp = requests.post("https://uguu.se/upload.php", files=files, headers=headers, timeout=20)
            if resp.status_code == 200:
                res_json = resp.json()
                if "files" in res_json and len(res_json["files"]) > 0:
                    u_url = res_json["files"][0].get("url")
                    if u_url and u_url.startswith("http"):
                        return u_url
    except Exception:
        pass

    # 3. Tentative Tier 3 : Litterbox
    try:
        url_litterbox = "https://litterbox.catbox.moe/resources/internals/api.php"
        with open(file_path, "rb") as f:
            files = {"fileToUpload": (file_path.name, f)}
            data = {"reqtype": "fileupload", "time": "24h"}
            resp = requests.post(url_litterbox, files=files, data=data, headers=headers, timeout=20)
            if resp.status_code == 200 and resp.text.startswith("http"):
                return resp.text.strip()
    except Exception:
        pass

    # 4. Tentative Tier 4 : Catbox
    try:
        url_catbox = "https://catbox.moe/user/api.php"
        with open(file_path, "rb") as f:
            files = {"fileToUpload": (file_path.name, f)}
            data = {"reqtype": "fileupload"}
            resp = requests.post(url_catbox, files=files, data=data, headers=headers, timeout=20)
            if resp.status_code == 200 and resp.text.startswith("http"):
                return resp.text.strip()
    except Exception:
        pass

    raise ImageBridgeError("Impossible d'obtenir une URL CDN publique pour l'image. Vérifiez votre connexion Internet.")

def process_image(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """Traite l'image locale, extrait ses dimensions et génère l'URL publique nécessaire à Super Video AI."""
    local_path = save_local_image(file_bytes, original_filename)
    public_url = upload_to_public_host(local_path)
    dimensions_data = get_image_dimensions_and_optimal_preset(local_path)
    
    result = {
        "filename": original_filename,
        "local_name": local_path.name,
        "local_path": str(local_path),
        "public_url": public_url,
        "size_bytes": len(file_bytes)
    }
    result.update(dimensions_data)
    return result

