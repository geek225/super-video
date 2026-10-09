import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import BASE_DIR, get_user_api_key, get_base_url, OUTPUTS_DIR
from app.security_vault import (
    get_default_query_url,
    get_default_model_id,
    resolve_candidate_keys,
    register_task_key,
    get_task_key,
    get_shared_quota_status,
    consume_shared_quota,
)


class AgnesAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class AgnesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = get_base_url()
        self.query_url = get_default_query_url()

    def _build_headers(self, key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def create_video_task(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model: str = "",
        mode: str = "keyframe",
        seconds: str = "5",
        size: str = "720P",
        aspect_ratio: str = "original",
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        seed: Optional[int] = None,
        motion_design_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Crée une tâche de génération vidéo asynchrone avec rotation multi-clés (Failover)
        et gestion du quota journalier sur le Pool partagé (Solution C).
        """
        default_model = get_default_model_id()
        active_model = default_model if model in ("", "default", "studio-v2.0") else model
        endpoint = f"{self.base_url}/videos"

        candidates, is_shared_pool = resolve_candidate_keys(self.api_key or get_user_api_key())
        if not candidates:
            raise AgnesAPIError(
                "Aucune clé Studio disponible. Veuillez renseigner une clé dans le bouton 'Clé Studio'.",
                status_code=401,
            )

        if is_shared_pool:
            used_today, limit_today = get_shared_quota_status(BASE_DIR)
            if used_today >= limit_today:
                raise AgnesAPIError(
                    f"Quota gratuit journalier atteint ({limit_today}/{limit_today} vidéos aujourd'hui sur le Pool partagé). "
                    "Revenez demain ou renseignez votre propre Clé Studio personnelle (bouton 'Clé Studio' en haut à droite) pour générer en illimité !",
                    status_code=429,
                )

        if motion_design_mode:
            final_prompt = (
                f"Strict cinematic motion design animation of the uploaded original image. "
                f"The existing characters' faces, facial bone structure, eyes, expressions, hairstyles, clothes, "
                f"uniforms, jersey numbers, skin tones, and overall composition are 100% locked, identical, and preserved across all frames. "
                f"Zero face morphing, zero identity change, zero aging, zero character drift, zero substitution, zero duplicate people. "
                f"The existing characters remain strictly in their exact poses and animate naturally with subtle chest breathing, "
                f"slight organic micro-motion in place, and focused gaze. The background environment comes alive with dynamic atmospheric lighting, "
                f"subtle depth parallax camera movement, and volumetric particles: {prompt}"
            )
            neg_prompt = (
                "face morphing, changing faces, face drift, changing facial identity, aging, transforming into someone else, "
                "character drift, face swap, new characters, different people, duplicate persons, malformed hands, distorted eyes, "
                "mutated faces, extra limbs, bad anatomy, deformed bodies, blur, low resolution, artifacts, visual glitches, cartoonish distortion"
            )
        else:
            final_prompt = prompt
            neg_prompt = "morphing, deformed faces, distorted bodies, changing characters, new people, mutation, blurry, bad anatomy, duplicate people, jittery, low quality"

        if active_model == default_model:
            sec_float = float(seconds) if seconds else 5.0
            approx_frames = int(sec_float * 24)
            n = max(10, (approx_frames - 1) // 8)
            num_frames = min(441, 8 * n + 1)

            if target_width and target_height:
                width, height = int(target_width), int(target_height)
            elif aspect_ratio == "1:1":
                width, height = 960, 960
            elif aspect_ratio == "3:4":
                width, height = 832, 1088
            elif aspect_ratio == "4:3":
                width, height = 1088, 832
            elif aspect_ratio == "9:16":
                width, height = 704, 1280
            elif aspect_ratio == "16:9":
                width, height = 1280, 704
            else:
                width, height = 960, 960

            payload: Dict[str, Any] = {
                "model": default_model,
                "prompt": final_prompt,
                "image": image_url,
                "height": height,
                "width": width,
                "num_frames": num_frames,
                "frame_rate": 24,
                "negative_prompt": neg_prompt,
            }
        else:
            payload = {
                "model": active_model,
                "prompt": final_prompt,
                "mode": mode,
                "seconds": str(seconds),
                "size": size,
                "aspect_ratio": aspect_ratio,
            }
            if image_url:
                if mode == "keyframe":
                    payload["first_frame"] = image_url
                elif mode == "reference":
                    payload["images"] = [image_url]
                else:
                    payload["image"] = image_url

        if seed is not None:
            payload["seed"] = seed

        last_error_msg = "Service temporairement saturé."
        last_status = 500

        # Rotation intelligente sur les clés disponibles (Failover transparent)
        for candidate_key in candidates:
            try:
                response = requests.post(
                    endpoint,
                    headers=self._build_headers(candidate_key),
                    json=payload,
                    timeout=90,
                )
            except requests.RequestException as e:
                last_error_msg = f"Erreur de connexion au serveur Super Video AI : {str(e)}"
                continue

            if response.status_code == 200:
                data = response.json()
                vid = data.get("video_id") or data.get("task_id") or data.get("id")
                if vid:
                    register_task_key(str(vid), candidate_key)
                if is_shared_pool:
                    consume_shared_quota(BASE_DIR)
                return data

            last_status = response.status_code
            try:
                err_data = response.json()
                msg = err_data.get("message") or err_data.get("error", {}).get("message") or str(err_data)
                code = err_data.get("code") or ""
                if "insufficient_user_quota" in msg or code == "insufficient_user_quota":
                    msg = "Quota épuisé sur cette clé. Passage à une autre clé ou sélectionnez 'Super Video Engine v2.0 (Standard HD - Inclus)'."
                last_error_msg = msg
            except Exception:
                last_error_msg = response.text or f"Erreur HTTP {response.status_code}"

            # Si erreur de quota/rate-limit (429/401/403/5xx), tester la clé suivante du Pool
            if response.status_code in (401, 402, 403, 429, 500, 502, 503, 504):
                continue
            else:
                break

        raise AgnesAPIError(f"Échec Super Video AI ({last_status}) : {last_error_msg}", status_code=last_status)

    def get_task_status(self, video_id: str, model: str = "") -> Dict[str, Any]:
        """Interroge l'état d'avancement de la tâche vidéo avec la clé associée."""
        default_model = get_default_model_id()
        active_model = default_model if model in ("", "default", "studio-v2.0") else model
        params = {
            "video_id": video_id,
            "model_name": active_model,
        }

        mapped_key = get_task_key(video_id)
        candidates, _ = resolve_candidate_keys(self.api_key or get_user_api_key())
        key_to_use = mapped_key or (candidates[0] if candidates else "")

        try:
            response = requests.get(
                self.query_url,
                headers=self._build_headers(key_to_use),
                params=params,
                timeout=30,
            )
        except requests.RequestException as e:
            raise AgnesAPIError(f"Erreur lors du suivi de la tâche : {str(e)}")

        if response.status_code != 200:
            try:
                err_data = response.json()
                msg = err_data.get("message") or err_data.get("error", {}).get("message") or str(err_data)
            except Exception:
                msg = response.text
            raise AgnesAPIError(f"Erreur lors de la récupération de la vidéo ({response.status_code}) : {msg}", status_code=response.status_code)

        result = response.json()
        video_url = result.get("url")
        if not video_url and isinstance(result.get("metadata"), dict):
            video_url = result.get("metadata", {}).get("url")

        result["resolved_url"] = video_url
        return result

    def download_and_save_video(self, video_url: str, video_id: str, meta: Dict[str, Any]) -> Path:
        """Télécharge le fichier MP4 généré et l'enregistre localement dans outputs/."""
        clean_id = "".join(c for c in video_id if c.isalnum() or c in "_-")
        timestamp = int(time.time())
        output_file = OUTPUTS_DIR / f"video_{timestamp}_{clean_id}.mp4"
        meta_file = OUTPUTS_DIR / f"video_{timestamp}_{clean_id}.json"

        try:
            with requests.get(video_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(output_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            meta["local_filename"] = output_file.name
            meta["saved_at"] = timestamp
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            return output_file
        except requests.RequestException as e:
            raise AgnesAPIError(f"Échec du téléchargement du fichier vidéo : {str(e)}")
