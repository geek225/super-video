import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import get_api_key, get_base_url, OUTPUTS_DIR

class AgnesAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

class AgnesClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        self.base_url = get_base_url()
        self.query_url = "https://apihub.agnes-ai.com/agnesapi"

    def _get_headers(self) -> Dict[str, str]:
        key = self.api_key or get_api_key()
        if not key:
            raise AgnesAPIError("Clé d'activation Studio manquante. Veuillez configurer votre clé dans les paramètres ou le fichier .env.")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def create_video_task(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        model: str = "agnes-video-v2.0",
        mode: str = "keyframe",
        seconds: str = "5",
        size: str = "720P",
        aspect_ratio: str = "original",
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        seed: Optional[int] = None,
        motion_design_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Crée une tâche de génération vidéo asynchrone sur Agnes AI.
        Prend en charge agnes-video-v2.0 (gratuit) et la série agnes-video-2.5.
        Le mode motion_design_mode verrouille strictement les personnages existants et leur décor.
        """
        endpoint = f"{self.base_url}/videos"
        
        # Application des consignes strictes de fidélité et d'anti-morphing pour motion design
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

        if model == "agnes-video-v2.0":
            # Spécifications pour agnes-video-v2.0 (modèle gratuit à $0/sec)
            sec_float = float(seconds) if seconds else 5.0
            # Règle Agnes AI : num_frames doit suivre la règle 8n + 1 et <= 441
            approx_frames = int(sec_float * 24)
            n = max(10, (approx_frames - 1) // 8)
            num_frames = min(441, 8 * n + 1)
            
            # Priorité aux dimensions cibles calculées depuis l'image originale
            if target_width and target_height:
                width, height = int(target_width), int(target_height)
            elif aspect_ratio == "1:1":
                width, height = 960, 960
            elif aspect_ratio == "3:4":
                width, height = 832, 1088  # Ratio vertical affiche
            elif aspect_ratio == "4:3":
                width, height = 1088, 832  # Ratio paysage standard
            elif aspect_ratio == "9:16":
                width, height = 704, 1280  # Ratio vertical story/short
            elif aspect_ratio == "16:9":
                width, height = 1280, 704  # Ratio cinéma/YouTube
            else:
                width, height = 960, 960  # Défaut équilibré sans rognage excessif

            payload: Dict[str, Any] = {
                "model": "agnes-video-v2.0",
                "prompt": final_prompt,
                "image": image_url,
                "height": height,
                "width": width,
                "num_frames": num_frames,
                "frame_rate": 24,
                "negative_prompt": neg_prompt
            }
        else:
            # Spécifications pour agnes-video-2.5
            payload = {
                "model": model,
                "prompt": final_prompt,
                "mode": mode,
                "seconds": str(seconds),
                "size": size,
                "aspect_ratio": aspect_ratio
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

        try:
            # Timeout étendu à 90 secondes pour éviter toute coupure réseau prématurée
            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=90
            )
        except requests.RequestException as e:
            raise AgnesAPIError(f"Erreur de connexion au serveur Super Video AI : {str(e)}")

        if response.status_code != 200:
            try:
                err_data = response.json()
                msg = err_data.get("message") or err_data.get("error", {}).get("message") or str(err_data)
                code = err_data.get("code") or ""
                if "insufficient_user_quota" in msg or code == "insufficient_user_quota":
                    msg = "Crédits insuffisants pour ce modèle haute fidélité. Sélectionnez 'Super Video Engine v2.0 (Standard HD - Inclus)' dans la liste des modèles pour générer immédiatement !"
            except Exception:
                msg = response.text or f"Erreur HTTP {response.status_code}"
            raise AgnesAPIError(f"Échec Super Video AI ({response.status_code}) : {msg}", status_code=response.status_code)

        data = response.json()
        return data

    def get_task_status(self, video_id: str, model: str = "agnes-video-2.5") -> Dict[str, Any]:
        """
        Interroge l'état d'avancement de la tâche vidéo.
        """
        params = {
            "video_id": video_id,
            "model_name": model
        }
        
        try:
            response = requests.get(
                self.query_url,
                headers=self._get_headers(),
                params=params,
                timeout=30
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
        
        # Extraction de l'URL finale (peut être au premier niveau ou dans metadata.url)
        video_url = result.get("url")
        if not video_url and isinstance(result.get("metadata"), dict):
            video_url = result.get("metadata", {}).get("url")
            
        result["resolved_url"] = video_url
        return result

    def download_and_save_video(self, video_url: str, video_id: str, meta: Dict[str, Any]) -> Path:
        """
        Télécharge le fichier MP4 généré et l'enregistre localement dans outputs/.
        """
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
                            
            # Sauvegarde des métadonnées locales
            meta["local_filename"] = output_file.name
            meta["saved_at"] = timestamp
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            return output_file
        except requests.RequestException as e:
            raise AgnesAPIError(f"Échec du téléchargement du fichier vidéo : {str(e)}")
