import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import (
    BASE_DIR,
    UPLOADS_DIR,
    OUTPUTS_DIR,
    PROVIDER_PRESETS,
    get_api_key,
    get_user_api_key,
    save_api_key,
    get_base_url,
    save_base_url,
    get_provider_mode,
    save_provider_mode,
    get_custom_model,
    save_custom_model,
    reset_to_free_pool,
)
from app.security_vault import (
    get_default_base_url,
    get_shared_quota_status,
    get_shared_pool_keys,
    resolve_candidate_keys,
)
from app.image_bridge import process_image, ImageBridgeError
from app.agnes_client import AgnesClient, AgnesAPIError
from app.updater import check_for_updates, apply_update

app = FastAPI(title="Super Video - Local Studio", version="1.0.0")

# Autoriser strictement les requêtes locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7860",
        "http://127.0.0.1:7860",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Montage des dossiers statiques et de stockage
STATIC_DIR = Path(__file__).parent / "static"
PUBLIC_DIR = BASE_DIR / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Description de l'animation")
    image_url: Optional[str] = Field(None, description="URL de l'image source")
    model: str = Field("studio-v2.0", description="Modèle Studio")
    mode: str = Field("keyframe", description="Mode de génération (keyframe, reference, text)")
    seconds: str = Field("5", description="Durée en secondes (4 à 12)")
    size: str = Field("720P", description="Résolution (720P, 1080P, 1K, 2K)")
    aspect_ratio: str = Field("original", description="Format d'image (original, 1:1, 3:4, 4:3, 9:16, 16:9)")
    target_width: Optional[int] = Field(None, description="Largeur cible explicite")
    target_height: Optional[int] = Field(None, description="Hauteur cible explicite")
    seed: Optional[int] = Field(None, description="Graine aléatoire")
    motion_design_mode: bool = Field(True, description="Mode motion design fidèle 100%")


class SettingsRequest(BaseModel):
    api_key: Optional[str] = Field(None, description="Clé Studio")
    base_url: Optional[str] = Field(None, description="URL de base du serveur")
    provider_mode: Optional[str] = Field(None, description="Identifiant du moteur (default, google_veo, openai_sora, kling_ai, higgsfield, fal_ai, custom)")
    custom_model: Optional[str] = Field(None, description="Identifiant du modèle cible")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Page introuvable")
    return HTMLResponse(
        content=index_file.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


@app.get("/api/settings")
async def get_settings():
    key = get_api_key()
    user_key = get_user_api_key()
    base_url = get_base_url()
    provider_mode = get_provider_mode()
    custom_model = get_custom_model()
    is_default = (base_url == get_default_base_url()) and (provider_mode in ("", "default"))
    _, is_shared_pool = resolve_candidate_keys(user_key)
    if not is_default:
        is_shared_pool = False

    configured = bool(user_key) if not is_default else bool(key)
    if not is_shared_pool and len(user_key) >= 8:
        masked = f"{user_key[:4]}...{user_key[-4:]}"
    elif configured:
        masked = "Pool Gratuit Actif"
    else:
        masked = "Non configurée"
    used_today, limit_today = get_shared_quota_status(BASE_DIR)
    return {
        "configured": configured,
        "masked_key": masked if configured else "",
        "base_url": "default" if is_default else base_url,
        "provider_mode": provider_mode or "default",
        "custom_model": custom_model,
        "is_default_engine": is_default,
        "is_shared_pool": is_shared_pool,
        "pool_size": len(get_shared_pool_keys()),
        "quota_used": used_today,
        "quota_limit": limit_today,
    }


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    updated = False
    if req.provider_mode is not None:
        pm = req.provider_mode.strip() or "default"
        save_provider_mode(pm)
        if pm in PROVIDER_PRESETS and pm != "custom":
            save_base_url(PROVIDER_PRESETS[pm] or "default")
        updated = True
    if req.base_url is not None and req.base_url.strip():
        save_base_url(req.base_url.strip())
        updated = True
    if req.custom_model is not None:
        save_custom_model(req.custom_model.strip())
        updated = True
    if req.api_key is not None and req.api_key.strip():
        save_api_key(req.api_key.strip())
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="Aucun paramètre à enregistrer.")

    return {"success": True, "message": "Paramètres enregistrés avec succès !"}


@app.post("/api/settings/reset")
async def reset_settings_to_pool():
    reset_to_free_pool()
    return {"success": True, "message": "Retour au Pool Gratuit Super Video AI (5 vidéos/jour) activé !"}


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Fichier vide.")
            
        data = process_image(file_bytes, file.filename or "image.png")
        data["preview_url"] = f"/uploads/{data['local_name']}"
        return JSONResponse(content={"success": True, "data": data})
    except ImageBridgeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de l'upload : {str(e)}")


@app.post("/api/generate")
async def create_video_task(req: GenerateRequest):
    key = get_api_key()
    if not key:
        raise HTTPException(status_code=401, detail="Clé d'activation Studio manquante. Veuillez la configurer dans les paramètres.")
    
    client = AgnesClient(api_key=get_user_api_key())
    try:
        task_data = client.create_video_task(
            prompt=req.prompt,
            image_url=req.image_url,
            model=req.model,
            mode=req.mode,
            seconds=req.seconds,
            size=req.size,
            aspect_ratio=req.aspect_ratio,
            target_width=req.target_width,
            target_height=req.target_height,
            seed=req.seed,
            motion_design_mode=req.motion_design_mode
        )
        return {"success": True, "data": task_data}
    except AgnesAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur inattendue : {str(e)}")


@app.get("/api/task/{video_id}")
async def check_task_status(video_id: str, model: str = "studio-v2.0"):
    client = AgnesClient()
    try:
        status_data = client.get_task_status(video_id, model=model)
        return status_data
    except AgnesAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@app.get("/api/stream/{video_id}")
async def stream_task_progress(video_id: str, model: str = "studio-v2.0"):
    """
    Flux Server-Sent Events (SSE) pour suivre l'avancement en temps réel
    et télécharger automatiquement le fichier MP4 dès qu'il est prêt.
    """
    async def event_generator():
        client = AgnesClient()
        max_attempts = 180  # 180 * 2s = ~6 minutes max
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                # Appel synchrone exécuté dans un thread pour ne pas bloquer l'async loop
                result = await asyncio.to_thread(client.get_task_status, video_id, model)
                status = result.get("status")
                progress = result.get("progress", 0)
                video_url = result.get("resolved_url")
                
                payload = {
                    "video_id": video_id,
                    "status": status,
                    "progress": progress,
                    "seconds": result.get("seconds"),
                    "size": result.get("size"),
                    "queue_message": result.get("queue_message"),
                }

                if status == "completed":
                    if video_url:
                        # Téléchargement local automatique
                        local_path = await asyncio.to_thread(
                            client.download_and_save_video,
                            video_url,
                            video_id,
                            result
                        )
                        payload["local_url"] = f"/outputs/{local_path.name}"
                        payload["remote_url"] = f"/outputs/{local_path.name}"
                        payload["filename"] = local_path.name
                    else:
                        payload["status"] = "failed"
                        payload["error"] = "Vidéo complétée mais URL introuvable."
                    
                    yield f"data: {json.dumps(payload)}\n\n"
                    break

                elif status == "failed":
                    payload["error"] = result.get("error", {}).get("message", "Échec de génération vidéo.")
                    yield f"data: {json.dumps(payload)}\n\n"
                    break
                
                else:
                    # En cours (queued, in_progress)
                    yield f"data: {json.dumps(payload)}\n\n"
                    
            except AgnesAPIError as e:
                err_payload = {"video_id": video_id, "status": "error", "message": str(e)}
                yield f"data: {json.dumps(err_payload)}\n\n"
            except Exception as e:
                err_payload = {"video_id": video_id, "status": "error", "message": str(e)}
                yield f"data: {json.dumps(err_payload)}\n\n"
                
            await asyncio.sleep(2)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/history")
async def get_history():
    """
    Retourne la liste des vidéos générées enregistrées localement dans outputs/.
    """
    items: List[Dict[str, Any]] = []
    
    for meta_file in sorted(OUTPUTS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                video_name = data.get("local_filename")
                if video_name and (OUTPUTS_DIR / video_name).exists():
                    items.append({
                        "id": data.get("video_id") or data.get("id"),
                        "video_url": f"/outputs/{video_name}",
                        "filename": video_name,
                        "saved_at": data.get("saved_at"),
                        "model": data.get("model"),
                        "seconds": data.get("seconds"),
                        "size": data.get("size")
                    })
        except Exception:
            continue
            
    return {"success": True, "history": items}


import sys
import subprocess


def _resolve_safe_output_file(filename: str) -> Path:
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."} or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide.")
    target = (OUTPUTS_DIR / safe_name).resolve()
    if OUTPUTS_DIR.resolve() not in target.parents or not target.exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo introuvable.")
    return target


@app.get("/api/download/{filename}")
async def download_video_file(filename: str):
    target = _resolve_safe_output_file(filename)
    return FileResponse(
        path=str(target),
        media_type="video/mp4",
        filename=target.name,
    )


@app.post("/api/reveal/{filename}")
async def reveal_video_in_folder(filename: str):
    target = _resolve_safe_output_file(filename)
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(target)], check=False)
        elif sys.platform == "win32":
            subprocess.run(["explorer.exe", f"/select,{str(target)}"], check=False)
        else:
            subprocess.run(["xdg-open", str(target.parent)], check=False)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impossible d'ouvrir le dossier : {str(e)}")


import importlib
from app import (
    security_vault as _sv_mod,
    config as _cfg_mod,
    image_bridge as _ib_mod,
    agnes_client as _ac_mod,
    updater as _upd_mod,
)


@app.get("/api/updates/check")
async def api_check_updates():
    return check_for_updates()


@app.post("/api/updates/apply")
async def api_apply_update():
    res = apply_update()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Échec de la mise à jour"))
    try:
        importlib.reload(_sv_mod)
        importlib.reload(_cfg_mod)
        importlib.reload(_ib_mod)
        importlib.reload(_ac_mod)
        importlib.reload(_upd_mod)
    except Exception:
        pass
    return res

