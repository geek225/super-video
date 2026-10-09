import base64
import io
import json
import threading
import time
import uuid
import urllib.parse
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
from app.config import (
    BASE_DIR,
    UPLOADS_DIR,
    OUTPUTS_DIR,
    get_user_api_key,
    get_base_url,
    get_provider_mode,
    get_custom_model,
)
from app.security_vault import (
    get_default_base_url,
    get_default_query_url,
    get_default_model_id,
    get_legacy_model_id,
    get_relay_node_urls,
    sanitize_provider_text,
    resolve_candidate_keys,
    register_task_key,
    get_task_key,
    get_shared_quota_status,
    consume_shared_quota,
)

# Suivi temps réel des tâches exécutées sur le Cluster GPU Relais Turbo
_RELAY_JOBS: Dict[str, Dict[str, Any]] = {}


class AgnesAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        clean_msg = sanitize_provider_text(message)
        super().__init__(clean_msg)
        self.status_code = status_code
        self.details = details


class AgnesClient:
    """
    Adaptateur Vidéo IA Universel Multi-Moteurs :
    - Super Video AI Cloud (Pool Gratuit 5 clés en rotation + File d'attente intelligente anti-503)
    - Google Veo 3 / Veo 2 (Google AI Studio / Gemini API directe sans Google Flow)
    - OpenAI Sora 2 / Sora Pro (API OpenAI Videos)
    - Kling AI (Kling 2.0 Master / 1.6 Image-to-Video)
    - Higgsfield AI (DoP Cinema / Diffuse)
    - Fal.ai Multi-Models (Veo 3, Kling, Runway Gen-3, Luma Ray 2, MiniMax Hailuo)
    - Serveurs Personnalisés compatibles /v1/videos
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = get_base_url()
        self.provider_mode = get_provider_mode()
        self.custom_model = get_custom_model()
        self.query_url = get_default_query_url()

    def _build_headers(self, key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _compile_prompts(self, prompt: str, motion_design_mode: bool) -> Tuple[str, str]:
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
        return final_prompt, neg_prompt

    def _load_image_base64(self, image_url: Optional[str]) -> Optional[Tuple[str, str]]:
        """Récupère les octets Base64 et le mimeType de l'image pour les moteurs directs (ex: Google Veo)."""
        if not image_url:
            return None
        try:
            recent_uploads = sorted(UPLOADS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for up in recent_uploads:
                if up.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    mime = "image/png" if up.suffix.lower() == ".png" else ("image/webp" if up.suffix.lower() == ".webp" else "image/jpeg")
                    return base64.b64encode(up.read_bytes()).decode("ascii"), mime

            if image_url.startswith("http"):
                r = requests.get(image_url, timeout=20)
                if r.status_code == 200:
                    ct = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                    return base64.b64encode(r.content).decode("ascii"), ct
        except Exception:
            pass
        return None

    # =========================================================================
    # ADAPTATEUR 1 : GOOGLE VEO 3 / VEO 2 (Direct Google AI Studio sans Flow)
    # =========================================================================
    def _create_google_veo_task(
        self,
        api_key: str,
        final_prompt: str,
        image_url: Optional[str],
        model: str,
        seconds: str,
        aspect_ratio: str,
    ) -> Dict[str, Any]:
        veo_models = []
        chosen = self.custom_model or model
        if chosen and "veo" in chosen.lower():
            veo_models.append(chosen)
        for fallback_m in ("veo-3.0-generate-preview", "veo-2.0-generate-001"):
            if fallback_m not in veo_models:
                veo_models.append(fallback_m)

        ar = "9:16" if aspect_ratio in ("9:16", "3:4") else "16:9"
        dur = 8 if float(seconds or 5) >= 7 else 5

        instance: Dict[str, Any] = {"prompt": final_prompt}
        img_data = self._load_image_base64(image_url)
        if img_data:
            b64_bytes, mime_type = img_data
            instance["image"] = {
                "bytesBase64Encoded": b64_bytes,
                "mimeType": mime_type,
            }

        payload = {
            "instances": [instance],
            "parameters": {
                "aspectRatio": ar,
                "durationSeconds": dur,
            },
        }

        base = self.base_url if "googleapis.com" in self.base_url else "https://generativelanguage.googleapis.com/v1beta"
        last_err = "Impossible de joindre Google Veo."
        last_code = 500

        for vm in veo_models:
            url = f"{base}/models/{vm}:predictLongRunning?key={urllib.parse.quote(api_key)}"
            try:
                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
            except requests.RequestException as e:
                last_err = str(e)
                continue

            if resp.status_code == 200:
                data = resp.json()
                op_name = data.get("name", "")
                vid = f"veo_op::{op_name}"
                register_task_key(vid, api_key)
                return {"video_id": vid, "status": "queued", "model": vm}

            last_code = resp.status_code
            try:
                last_err = resp.json().get("error", {}).get("message") or resp.text
            except Exception:
                last_err = resp.text

        raise AgnesAPIError(f"Erreur Google Veo ({last_code}) : {last_err}", status_code=last_code)

    def _poll_google_veo_task(self, video_id: str, api_key: str) -> Dict[str, Any]:
        op_name = video_id.split("veo_op::", 1)[1]
        base = self.base_url if "googleapis.com" in self.base_url else "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base}/{op_name.lstrip('/')}?key={urllib.parse.quote(api_key)}"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise AgnesAPIError(f"Erreur suivi Google Veo ({resp.status_code}) : {resp.text}", status_code=resp.status_code)

        data = resp.json()
        if not data.get("done"):
            return {"video_id": video_id, "status": "in_progress", "progress": 50}

        if "error" in data:
            err_msg = data["error"].get("message", str(data["error"]))
            return {"video_id": video_id, "status": "failed", "error": {"message": sanitize_provider_text(err_msg)}}

        resp_obj = data.get("response", {})
        samples = (
            resp_obj.get("generateVideoResponse", {}).get("generatedSamples")
            or resp_obj.get("generatedSamples")
            or resp_obj.get("videos")
            or []
        )
        video_uri = None
        if samples and isinstance(samples, list):
            first = samples[0]
            video_uri = first.get("video", {}).get("uri") or first.get("uri") or first.get("url")

        if video_uri and "googleapis.com" in video_uri and "key=" not in video_uri:
            sep = "&" if "?" in video_uri else "?"
            video_uri = f"{video_uri}{sep}key={urllib.parse.quote(api_key)}"

        return {
            "video_id": video_id,
            "status": "completed" if video_uri else "failed",
            "progress": 100,
            "resolved_url": video_uri,
        }

    # =========================================================================
    # ADAPTATEUR 2 : FAL.AI QUEUE (Veo 3, Kling 2.0, Runway, Luma, Hailuo)
    # =========================================================================
    def _create_fal_task(
        self,
        api_key: str,
        final_prompt: str,
        image_url: Optional[str],
        model: str,
        seconds: str,
        aspect_ratio: str,
    ) -> Dict[str, Any]:
        chosen = self.custom_model or model
        if not chosen or chosen in ("studio-v2.0", "default"):
            chosen = "fal-ai/kling-video/v2/master/image-to-video"
        elif not chosen.startswith("fal-ai/"):
            mapping = {
                "veo3": "fal-ai/veo3",
                "veo-3": "fal-ai/veo3",
                "kling-v2": "fal-ai/kling-video/v2/master/image-to-video",
                "runway-gen3": "fal-ai/runway-gen3/turbo/image-to-video",
                "luma-ray2": "fal-ai/luma-dream-machine/ray-2/image-to-video",
                "hailuo-minimax": "fal-ai/minimax/video-01-live/image-to-video",
            }
            chosen = mapping.get(chosen.lower(), f"fal-ai/{chosen.lstrip('/')}")

        endpoint = f"https://queue.fal.run/{chosen.lstrip('/')}"
        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "prompt": final_prompt,
            "image_url": image_url,
            "duration": "10" if float(seconds or 5) >= 8 else "5",
            "aspect_ratio": "9:16" if aspect_ratio in ("9:16", "3:4") else ("1:1" if aspect_ratio == "1:1" else "16:9"),
        }
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        if resp.status_code not in (200, 201, 202):
            raise AgnesAPIError(f"Erreur Fal.ai ({resp.status_code}) : {resp.text}", status_code=resp.status_code)

        data = resp.json()
        req_id = data.get("request_id", "")
        status_url = data.get("status_url") or f"{endpoint}/requests/{req_id}/status"
        response_url = data.get("response_url") or f"{endpoint}/requests/{req_id}"
        encoded_ref = base64.urlsafe_b64encode(json.dumps({"s": status_url, "r": response_url}).encode("utf-8")).decode("ascii")
        vid = f"fal_op::{encoded_ref}"
        register_task_key(vid, api_key)
        return {"video_id": vid, "status": "queued", "model": chosen}

    def _poll_fal_task(self, video_id: str, api_key: str) -> Dict[str, Any]:
        encoded_ref = video_id.split("fal_op::", 1)[1]
        urls = json.loads(base64.urlsafe_b64decode(encoded_ref.encode("ascii")).decode("utf-8"))
        headers = {"Authorization": f"Key {api_key}"}

        s_resp = requests.get(urls["s"], headers=headers, timeout=30)
        if s_resp.status_code != 200:
            raise AgnesAPIError(f"Erreur statut Fal.ai ({s_resp.status_code}) : {s_resp.text}", status_code=s_resp.status_code)

        s_data = s_resp.json()
        st = (s_data.get("status") or "").upper()
        if st in ("IN_QUEUE", "PENDING"):
            return {"video_id": video_id, "status": "queued", "progress": 15}
        if st == "IN_PROGRESS":
            return {"video_id": video_id, "status": "in_progress", "progress": 60}
        if st == "COMPLETED":
            r_resp = requests.get(urls["r"], headers=headers, timeout=30)
            r_data = r_resp.json() if r_resp.status_code == 200 else {}
            video_url = (
                (r_data.get("video") or {}).get("url")
                if isinstance(r_data.get("video"), dict)
                else r_data.get("video_url") or r_data.get("url")
            )
            return {
                "video_id": video_id,
                "status": "completed" if video_url else "failed",
                "progress": 100,
                "resolved_url": video_url,
            }
        return {"video_id": video_id, "status": "failed", "error": {"message": sanitize_provider_text(str(s_data))}}

    # =========================================================================
    # CONSTRUCTION DU PAYLOAD POUR LE SERVEUR PAR DÉFAUT OU COMPATIBLE /v1/videos
    # =========================================================================
    def _build_video_payload(
        self,
        active_model: str,
        final_prompt: str,
        neg_prompt: str,
        image_url: Optional[str],
        mode: str,
        seconds: str,
        size: str,
        aspect_ratio: str,
        target_width: Optional[int],
        target_height: Optional[int],
        seed: Optional[int],
    ) -> Dict[str, Any]:
        legacy_model = get_legacy_model_id()

        # Déterminer le ratio explicite (1:1, 3:4, 4:3, 9:16, 16:9) à partir des dimensions si "original"
        resolved_ar = aspect_ratio
        if resolved_ar == "original":
            if target_width and target_height:
                r = float(target_width) / float(target_height)
                if r >= 1.55:
                    resolved_ar = "16:9"
                elif r >= 1.15:
                    resolved_ar = "4:3"
                elif r >= 0.85:
                    resolved_ar = "1:1"
                elif r >= 0.65:
                    resolved_ar = "3:4"
                else:
                    resolved_ar = "9:16"
            else:
                resolved_ar = "1:1"

        if active_model == legacy_model:
            sec_float = float(seconds) if seconds else 5.0
            approx_frames = int(sec_float * 24)
            n = max(10, (approx_frames - 1) // 8)
            num_frames = min(441, 8 * n + 1)

            if target_width and target_height:
                width, height = int(target_width), int(target_height)
            elif resolved_ar == "1:1":
                width, height = 960, 960
            elif resolved_ar == "3:4":
                width, height = 832, 1088
            elif resolved_ar == "4:3":
                width, height = 1088, 832
            elif resolved_ar == "9:16":
                width, height = 704, 1280
            else:
                width, height = 1280, 704

            payload: Dict[str, Any] = {
                "model": legacy_model,
                "prompt": final_prompt,
                "image": image_url,
                "height": height,
                "width": width,
                "num_frames": num_frames,
                "frame_rate": 24,
                "negative_prompt": neg_prompt,
            }
        else:
            # Format standard 2.5-flash / Sora / Kling / Higgsfield
            sec_int = int(round(float(seconds or 5)))
            clean_sec = "10" if sec_int >= 8 else "5"
            payload = {
                "model": active_model,
                "prompt": final_prompt,
                "mode": mode or "keyframe",
                "seconds": clean_sec,
                "size": size if size in ("720P", "1080P") else "720P",
                "aspect_ratio": resolved_ar,
            }
            if image_url:
                if mode == "reference":
                    payload["images"] = [image_url]
                else:
                    payload["first_frame"] = image_url

        if seed is not None:
            payload["seed"] = seed
        return payload

    def _try_submit_once(
        self,
        endpoint: str,
        candidate_key: str,
        payload: Dict[str, Any],
        is_default_server: bool,
        is_shared_pool: bool,
    ) -> Tuple[Optional[Dict[str, Any]], int, str, str]:
        """Tente un appel POST unique. Retourne (data_si_succès, status_code, error_code, error_msg)."""
        req_timeout = 15 if is_default_server else 60
        try:
            response = requests.post(
                endpoint,
                headers=self._build_headers(candidate_key),
                json=payload,
                timeout=req_timeout,
            )
        except requests.RequestException as e:
            return None, 503, "network_error", sanitize_provider_text(str(e))

        if response.status_code in (200, 201, 202):
            data = response.json()
            vid = data.get("video_id") or data.get("task_id") or data.get("id")
            if vid:
                if not is_default_server:
                    vid = f"custom_op::{vid}"
                    data["video_id"] = vid
                register_task_key(str(vid), candidate_key)
                data["used_model"] = payload.get("model", "")
            if is_shared_pool:
                consume_shared_quota(BASE_DIR)
            return data, 200, "", ""

        err_code = ""
        err_msg = ""
        try:
            err_data = response.json()
            err_code = err_data.get("code") or (err_data.get("error") or {}).get("code") or ""
            err_msg = (
                err_data.get("message")
                or (err_data.get("error") or {}).get("message")
                or str(err_data)
            )
        except Exception:
            err_msg = response.text or f"Erreur HTTP {response.status_code}"

        return None, response.status_code, str(err_code), sanitize_provider_text(str(err_msg))

    # =========================================================================
    # CLUSTER GPU RELAIS TURBO (Bascule instantanée anti-503 / anti-429)
    # =========================================================================
    def _resolve_relay_image_bytes(
        self,
        image_url: Optional[str],
        width: int,
        height: int,
    ) -> Tuple[str, bytes, str]:
        """Récupère les octets de l'image locale uploadée (ou génère un canevas cinéma si mode texte)."""
        try:
            recent_uploads = sorted(UPLOADS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for up in recent_uploads:
                if up.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and up.stat().st_size > 0:
                    mime = (
                        "image/png"
                        if up.suffix.lower() == ".png"
                        else ("image/webp" if up.suffix.lower() == ".webp" else "image/jpeg")
                    )
                    return up.name, up.read_bytes(), mime
        except Exception:
            pass

        if image_url and image_url.startswith("http"):
            try:
                r = requests.get(image_url, timeout=15)
                if r.status_code == 200 and r.content:
                    ct = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                    ext = ".png" if "png" in ct else ".jpg"
                    return f"input_frame{ext}", r.content, ct
            except Exception:
                pass

        # Canevas par défaut si aucune image n'est fournie
        buf = io.BytesIO()
        canvas = Image.new("RGB", (max(512, width), max(512, height)), (14, 16, 28))
        canvas.save(buf, format="JPEG", quality=92)
        return "canvas.jpg", buf.getvalue(), "image/jpeg"

    @staticmethod
    def _extract_relay_video_url(node_url: str, data_obj: Any) -> Optional[str]:
        """Extrait l'URL MP4 finale depuis la réponse d'un nœud GPU Relais."""
        if not data_obj:
            return None
        first = data_obj[0] if isinstance(data_obj, list) and len(data_obj) > 0 else data_obj
        if isinstance(first, dict) and isinstance(first.get("video"), dict):
            first = first["video"]
        if isinstance(first, dict):
            v_url = first.get("url")
            v_path = first.get("path")
            if v_url and str(v_url).startswith("http"):
                return str(v_url)
            if v_path:
                return f"{node_url.rstrip('/')}/gradio_api/file={v_path}"
        return None

    def _run_cloud_relay_worker(
        self,
        relay_id: str,
        final_prompt: str,
        neg_prompt: str,
        image_url: Optional[str],
        seconds: str,
        size: str,
        aspect_ratio: str,
        target_width: Optional[int],
        target_height: Optional[int],
        seed: Optional[int],
        is_shared_pool: bool,
    ) -> None:
        job = _RELAY_JOBS.get(relay_id)
        if not job:
            return

        w = int(target_width or 832)
        h = int(target_height or 1088)
        if not target_width or not target_height:
            if aspect_ratio == "16:9":
                w, h = 896, 512
            elif aspect_ratio == "9:16":
                w, h = 512, 896
            elif aspect_ratio == "1:1":
                w, h = 704, 704

        fname, img_bytes, mime_type = self._resolve_relay_image_bytes(image_url, w, h)
        nodes = get_relay_node_urls()
        dur_sec = min(5.0, max(2.5, float(seconds or 5.0)))
        seed_val = int(seed) if seed is not None else 42
        randomize = seed is None
        last_error = "Tous les nœuds GPU sont temporairement occupés."

        for node_idx, node_url in enumerate(nodes):
            try:
                job["progress"] = max(job.get("progress", 14), 16 + node_idx * 4)
                job["queue_message"] = f"Connexion au Cluster GPU Turbo Super Video AI (Nœud #{node_idx + 1})..."

                # 1. Envoi de l'image source sur le nœud GPU
                files = {"files": (fname, img_bytes, mime_type)}
                r_up = requests.post(f"{node_url}/gradio_api/upload", files=files, timeout=25)
                if r_up.status_code != 200:
                    last_error = f"Nœud #{node_idx + 1} indisponible (upload {r_up.status_code})"
                    continue
                up_list = r_up.json()
                if not isinstance(up_list, list) or not up_list:
                    continue
                remote_path = up_list[0]

                job["progress"] = max(job.get("progress", 22), 26)
                job["queue_message"] = "Image verrouillée sur le GPU — lancement du moteur Motion Design..."

                # 2. Construction des paramètres selon la signature du nœud GPU
                file_obj = {"path": remote_path, "meta": {"_type": "gradio.FileData"}}
                if "multimodalart-wan2-1-fast" in node_url:
                    # Nœud Wan 2.1 Fast (10 paramètres)
                    norm_h = max(384, min(896, (h // 32) * 32))
                    norm_w = max(384, min(896, (w // 32) * 32))
                    call_data = [
                        file_obj,
                        final_prompt,
                        norm_h,
                        norm_w,
                        neg_prompt,
                        min(4, max(2, int(round(dur_sec)))),
                        1.0,
                        4,
                        seed_val,
                        randomize,
                    ]
                elif "r3gm-wan2-2" in node_url:
                    # Nœud Wan 2.2 Preview (17 paramètres)
                    call_data = [
                        file_obj,
                        None,
                        final_prompt,
                        6,
                        neg_prompt,
                        dur_sec,
                        1,
                        1,
                        seed_val,
                        randomize,
                        6,
                        "UniPCMultistep",
                        3.0,
                        16,
                        True,
                        True,
                        True,
                    ]
                else:
                    # Nœud principal Wan 2.2 FP8 AOTI Faster (9 paramètres)
                    call_data = [
                        file_obj,
                        final_prompt,
                        6,
                        neg_prompt,
                        dur_sec,
                        1.0,
                        1.0,
                        seed_val,
                        randomize,
                    ]

                r_call = requests.post(
                    f"{node_url}/gradio_api/call/generate_video",
                    json={"data": call_data},
                    timeout=25,
                )
                if r_call.status_code != 200:
                    last_error = f"Nœud #{node_idx + 1} occupé ({r_call.status_code})"
                    continue

                event_id = r_call.json().get("event_id")
                if not event_id:
                    continue

                job["progress"] = max(job.get("progress", 32), 34)
                job["queue_message"] = "Calcul GPU haute vitesse en cours (animation et effets de lumière)..."

                # 3. Lecture du flux SSE du nœud GPU
                current_event = ""
                node_failed = False
                with requests.get(
                    f"{node_url}/gradio_api/call/generate_video/{event_id}",
                    stream=True,
                    timeout=150,
                ) as s_resp:
                    for raw_line in s_resp.iter_lines(decode_unicode=True):
                        if not raw_line:
                            continue
                        line = raw_line.strip()
                        if line.startswith("event:"):
                            current_event = line.split("event:", 1)[1].strip()
                            if current_event == "heartbeat":
                                cur_p = int(job.get("progress", 35))
                                job["progress"] = min(90, cur_p + 12)
                                job["queue_message"] = "Rendu des images clés HD sur le GPU Turbo..."
                        elif line.startswith("data:"):
                            data_str = line.split("data:", 1)[1].strip()
                            if current_event == "error":
                                last_error = sanitize_provider_text(data_str or "Erreur sur le nœud GPU")
                                node_failed = True
                                break
                            if current_event == "complete" and data_str and data_str != "null":
                                parsed = json.loads(data_str)
                                video_url = self._extract_relay_video_url(node_url, parsed)
                                if video_url:
                                    if is_shared_pool:
                                        consume_shared_quota(BASE_DIR)
                                    job["progress"] = 100
                                    job["status"] = "completed"
                                    job["resolved_url"] = video_url
                                    job["queue_message"] = "Rendu terminé avec succès !"
                                    return
                                else:
                                    node_failed = True
                                    break
                if node_failed:
                    continue
            except Exception as e:
                last_error = sanitize_provider_text(str(e))
                continue

        job["status"] = "failed"
        job["error"] = {
            "message": (
                f"Les serveurs gratuits Super Video AI sont momentanément saturés ({last_error}). "
                "Veuillez réessayer dans un instant ou connecter une clé personnelle dans 'Studio Actif'."
            )
        }

    def _launch_cloud_relay_job(
        self,
        final_prompt: str,
        neg_prompt: str,
        image_url: Optional[str],
        seconds: str,
        size: str,
        aspect_ratio: str,
        target_width: Optional[int],
        target_height: Optional[int],
        seed: Optional[int],
        is_shared_pool: bool,
        raw_prompt: str = "",
    ) -> Dict[str, Any]:
        relay_id = f"relay::{uuid.uuid4().hex[:12]}"
        _RELAY_JOBS[relay_id] = {
            "video_id": relay_id,
            "status": "in_progress",
            "progress": 14,
            "prompt": raw_prompt or final_prompt,
            "seconds": str(seconds or "5"),
            "size": size or "720P",
            "started_at": time.time(),
            "resolved_url": None,
            "error": None,
            "queue_message": "Bascule automatique sur le Cluster GPU Turbo Super Video AI...",
        }
        worker = threading.Thread(
            target=self._run_cloud_relay_worker,
            args=(
                relay_id,
                final_prompt,
                neg_prompt,
                image_url,
                seconds,
                size,
                aspect_ratio,
                target_width,
                target_height,
                seed,
                is_shared_pool,
            ),
            daemon=True,
        )
        worker.start()
        return {
            "video_id": relay_id,
            "status": "in_progress",
            "model": "studio-v2.0",
        }

    def _poll_cloud_relay_job(self, relay_id: str) -> Dict[str, Any]:
        job = _RELAY_JOBS.get(relay_id)
        if not job:
            return {
                "video_id": relay_id,
                "status": "failed",
                "error": {"message": "La session de rendu a expiré. Veuillez relancer la génération."},
            }

        if job["status"] in ("completed", "failed"):
            return dict(job)

        # Progression fluide basée sur le temps écoulé (environ 55-65s pour un rendu Wan 2.2 complet)
        elapsed = max(0.0, time.time() - float(job.get("started_at", time.time())))
        time_based_progress = min(92, int(15 + elapsed * 1.25))
        job["progress"] = max(int(job.get("progress", 15)), time_based_progress)
        return dict(job)

    # =========================================================================
    # CRÉATION & SUIVI DE TÂCHE PRINCIPALE
    # =========================================================================
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
        final_prompt, neg_prompt = self._compile_prompts(prompt, motion_design_mode)
        user_key = (self.api_key or get_user_api_key()).strip()
        is_default_server = (self.base_url == get_default_base_url()) and (self.provider_mode in ("", "default"))

        # Cas 1 : Google Veo (Clé AIza... ou mode google_veo)
        if self.provider_mode == "google_veo" or "googleapis.com" in self.base_url or user_key.startswith("AIza"):
            if not user_key:
                raise AgnesAPIError("Veuillez renseigner votre clé API Google AI Studio (AIza...) dans 'Clé Studio'.", status_code=401)
            return self._create_google_veo_task(user_key, final_prompt, image_url, model, seconds, aspect_ratio)

        # Cas 2 : Fal.ai Multi-Modèles
        if self.provider_mode == "fal_ai" or "fal.run" in self.base_url:
            if not user_key:
                raise AgnesAPIError("Veuillez renseigner votre clé API Fal.ai dans 'Clé Studio'.", status_code=401)
            return self._create_fal_task(user_key, final_prompt, image_url, model, seconds, aspect_ratio)

        # Cas 3 : Pool Officiel Super Video AI ou Serveurs /v1/videos (Sora 2, Kling, Higgsfield, Hub Custom)
        default_model = get_default_model_id()
        legacy_model = get_legacy_model_id()

        if not is_default_server:
            default_map = {
                "openai_sora": "sora-2",
                "kling_ai": "kling-v2",
                "higgsfield": "higgsfield-dop",
            }
            active_model = self.custom_model or (
                default_map.get(self.provider_mode, model)
                if model in ("", "default", "studio-v2.0")
                else model
            )
            if not active_model or active_model in ("default", "studio-v2.0"):
                active_model = "sora-2"
            models_to_try = [active_model]
        else:
            if model in ("", "default", "studio-v2.0"):
                models_to_try = [default_model, legacy_model]
            else:
                models_to_try = [model, default_model]

        endpoint = f"{self.base_url}/videos"

        if is_default_server:
            candidates, is_shared_pool = resolve_candidate_keys(user_key)
        else:
            custom_keys = [k.strip() for k in user_key.split(",") if k.strip()]
            candidates, is_shared_pool = custom_keys, False

        if not candidates:
            raise AgnesAPIError(
                "Aucune clé d'activation disponible pour ce serveur. Veuillez renseigner votre clé dans 'Studio Actif'.",
                status_code=401,
            )

        if is_shared_pool:
            used_today, limit_today = get_shared_quota_status(BASE_DIR)
            if used_today >= limit_today:
                raise AgnesAPIError(
                    f"Quota gratuit journalier atteint ({limit_today}/{limit_today} vidéos aujourd'hui sur le Pool partagé). "
                    "Revenez demain ou connectez votre propre Clé / Serveur (Veo 3, Sora, Kling, Fal.ai) pour générer en illimité !",
                    status_code=429,
                )

        # Première tentative immédiate avec la première clé candidate sur le serveur primaire
        first_key = candidates[0]
        primary_payload = self._build_video_payload(
            models_to_try[0],
            final_prompt,
            neg_prompt,
            image_url,
            mode,
            seconds,
            size,
            aspect_ratio,
            target_width,
            target_height,
            seed,
        )
        ok_data, status_code, err_code, err_msg = self._try_submit_once(
            endpoint, first_key, primary_payload, is_default_server, is_shared_pool
        )
        if ok_data is not None:
            return ok_data

        # Si le serveur primaire est saturé (video_queue_full / 503 / 429 / 403), bascule IMMÉDIATE
        # sur le Cluster GPU Relais Turbo pour générer la vidéo en ~60s sans attente bloquée à 10% !
        if is_default_server and status_code in (400, 402, 403, 429, 500, 502, 503, 504):
            return self._launch_cloud_relay_job(
                final_prompt=final_prompt,
                neg_prompt=neg_prompt,
                image_url=image_url,
                seconds=seconds,
                size=size,
                aspect_ratio=aspect_ratio,
                target_width=target_width,
                target_height=target_height,
                seed=seed,
                is_shared_pool=is_shared_pool,
                raw_prompt=prompt,
            )

        raise AgnesAPIError(f"Échec de génération ({status_code}) : {err_msg}", status_code=status_code)

    def get_task_status(self, video_id: str, model: str = "") -> Dict[str, Any]:
        """Interroge l'état d'avancement de la tâche vidéo quel que soit le moteur sélectionné."""
        if video_id.startswith("relay::") or video_id.startswith("autoqueue::"):
            return self._poll_cloud_relay_job(video_id)

        mapped_key = get_task_key(video_id)
        candidates, _ = resolve_candidate_keys(self.api_key or get_user_api_key())
        key_to_use = mapped_key or (candidates[0] if candidates else "")

        if video_id.startswith("veo_op::"):
            return self._poll_google_veo_task(video_id, key_to_use)

        if video_id.startswith("fal_op::"):
            return self._poll_fal_task(video_id, key_to_use)

        if video_id.startswith("custom_op::"):
            raw_id = video_id.split("custom_op::", 1)[1]
            try:
                r1 = requests.get(f"{self.base_url}/videos/{raw_id}", headers=self._build_headers(key_to_use), timeout=30)
                if r1.status_code == 200:
                    res = r1.json()
                    v_url = res.get("url") or res.get("video_url") or (res.get("output") or {}).get("url")
                    if not v_url and res.get("status") == "completed":
                        v_url = f"{self.base_url}/videos/{raw_id}/content"
                    res["resolved_url"] = v_url
                    return res
            except Exception:
                pass
            video_id_for_query = raw_id
        else:
            video_id_for_query = video_id

        default_model = get_default_model_id()
        active_model = default_model if model in ("", "default", "studio-v2.0") else model
        params = {
            "video_id": video_id_for_query,
            "model_name": active_model,
        }

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
        clean_id = "".join(c for c in video_id if c.isalnum() or c in "_-")[:48]
        timestamp = int(time.time())
        output_file = OUTPUTS_DIR / f"video_{timestamp}_{clean_id}.mp4"
        meta_file = OUTPUTS_DIR / f"video_{timestamp}_{clean_id}.json"

        mapped_key = get_task_key(video_id)
        dl_headers = {}
        if mapped_key and "/videos/" in video_url and "/content" in video_url:
            dl_headers["Authorization"] = f"Bearer {mapped_key}"

        try:
            with requests.get(video_url, headers=dl_headers, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(output_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            safe_meta = dict(meta)
            safe_meta["local_filename"] = output_file.name
            safe_meta["saved_at"] = timestamp
            safe_meta["resolved_url"] = f"/outputs/{output_file.name}"
            if "url" in safe_meta:
                safe_meta["url"] = f"/outputs/{output_file.name}"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(safe_meta, f, indent=2, ensure_ascii=False)

            return output_file
        except requests.RequestException as e:
            raise AgnesAPIError(f"Échec du téléchargement du fichier vidéo : {str(e)}")
