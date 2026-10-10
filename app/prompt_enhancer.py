import asyncio
import json
import logging
import random
import re
from typing import Optional, Dict, Any, List
import httpx

from app.security_vault import get_writer_base_url, get_writer_api_key

logger = logging.getLogger("supervideo.prompt_enhancer")

# Liste invisible des modèles gratuits ordonnée du MEILLEUR au plus rapide
FREE_MODELS_PRIORITY: List[str] = [
    "qwen/qwen3.8-omni-flash:free",   # Multimodal haute vitesse & cinématographie d'élite (instantané)
    "qwen/qwen3.8-max:free",          # Modèle flagship puissance maximale
    "qwen/qwen3.7-max:free",          # Haute qualité cinématographique
    "qwen/qwen3.7-flash:free",        # Rapide et percutant
    "qwen/qwen3.7-plus:free",         # Équilibré et riche en détails
    "qwen/qwen3.6-plus:free",         # Modèle de secours solide
    "qwen/qwen3.5-plus:free",         # Secours
    "qwen/qwen3.5-flash:free",        # Secours haute vitesse
    "meta/muse-spark-1.3-contributor:free",
    "liquid/lfm-2.5-2.6b:free",
]

SYSTEM_PROMPT = """Tu es le Rédacteur IA Super Video, un réalisateur et directeur artistique expert en animation vidéo IA cinématographique et Motion Design.
Ta mission : Transformer l'idée brute fournie par l'utilisateur en un prompt cinématographique d'élite pour modèle de génération vidéo (type Wan2.1, Runway Gen-3, Sora).

Directives strictes :
1. Reste fidèle à l'intention originale de l'utilisateur tout en sublimant l'éclairage, la caméra, l'atmosphère et les micro-mouvements.
2. Structure la description en 1 à 3 phrases fluides, percutantes et ultra-visuelles en français.
3. Inclus :
   - Mouvement de caméra (ex: travelling avant lent, panoramique fluide, léger travelling orbital, caméra à l'épaule stabilisée).
   - Éclairage et atmosphère (ex: lumière rasante dorée, néons brumeux, reflets anamorphiques, particules en suspension).
   - Dynamique des matières ou du sujet (ex: vent subtil dans les tissus, micro-expressions, reflets mouvants).
4. Ne mets AUCUN préambule, AUCUNE formule de politesse, AUCUN guillemet, AUCUN commentaire d'introduction ("Voici le prompt :"). Donne UNIQUEMENT le texte final prêt à être généré.
"""


def _local_fallback_enhancer(raw_prompt: str, mode: str = "cinema") -> str:
    """Moteur de secours local hors-ligne en cas de coupure réseau complète."""
    prompt = (raw_prompt or "").strip()
    if not prompt:
        prompt = "Un sujet principal élégant et captivant"

    cameras = [
        "Un travelling avant fluide et cinématographique",
        "Une caméra sur dolly avec une profondeur de champ anamorphique",
        "Un panoramique lent à 24fps au ralenti majestueux",
        "Un plan fixe contemplatif avec micro-parallaxe 3D",
    ]
    lights = [
        "baigné par une lumière rasante dorée de fin de journée",
        "éclairé par des projecteurs cinématiques avec une légère brume volumétrique",
        "sublimé par des reflets néons doux et des particules lumineuses en suspension",
        "dans une atmosphère contrastée aux ombres douces et dégradés profonds",
    ]
    details = [
        "les micro-mouvements organiques et les textures restent d'une netteté photographique 4K.",
        "une brise subtile anime délicatement l'arrière-plan sans déformer le sujet.",
        "les reflets et nuances d'ombres bougent avec un réalisme parfait.",
    ]

    cam = random.choice(cameras)
    light = random.choice(lights)
    det = random.choice(details)

    return f"{cam} capture {prompt}, {light}, tandis que {det}"


async def enhance_prompt_auto(raw_prompt: str, mode: str = "cinema", scene_number: int = 1) -> Dict[str, Any]:
    """
    Améliore automatiquement le prompt en sélectionnant de façon invisible
    le meilleur modèle gratuit disponible avec bascule automatique instantanée.
    """
    cleaned_input = (raw_prompt or "").strip()
    if not cleaned_input:
        cleaned_input = f"Scène {scene_number} : action cinématique vivante et percutante"

    base_url = get_writer_base_url()
    api_key = get_writer_api_key()

    if not api_key:
        logger.warning("Clé Rédacteur IA non configurée, bascule sur le moteur local")
        return {
            "success": True,
            "enhanced_prompt": _local_fallback_enhancer(cleaned_input, mode),
            "model_used": "local-cinematic-engine",
        }

    completions_url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) SuperVideoAI/2.0",
    }

    user_message = f"Améliore ce prompt pour la Scène {scene_number} (Mode: {mode}) : \"{cleaned_input}\""

    timeout_config = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=5.0)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        # Sélecteur invisible séquentiel : essaie le meilleur modèle d'abord, puis cascader
        for model_id in FREE_MODELS_PRIORITY:
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 180,
                "temperature": 0.7,
            }

            try:
                resp = await client.post(completions_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        content = re.sub(
                            r'^(Prompt\s*(amélioré|cinématique)?\s*:\s*|["\']|Voici\s+le\s+prompt\s*:\s*)',
                            '',
                            content,
                            flags=re.I
                        ).strip()
                        content = content.rstrip('"\'')
                        if content:
                            logger.info("Succès Rédacteur IA avec le modèle invisible: %s", model_id)
                            return {
                                "success": True,
                                "enhanced_prompt": content,
                                "model_used": model_id,
                            }
            except Exception as e:
                logger.warning("Modèle %s indisponible (%s), bascule sur le suivant...", model_id, e)
                continue

    # Si tous les modèles distants sont injoignables, fallback local transparent
    logger.info("Tous les modèles gratuits distants ont échoué, activation du moteur local")
    return {
        "success": True,
        "enhanced_prompt": _local_fallback_enhancer(cleaned_input, mode),
        "model_used": "local-cinematic-engine",
    }
