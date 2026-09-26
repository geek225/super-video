import io
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional
import requests

GITHUB_REPO = "geek225/super-video"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_current_git_commit() -> Optional[str]:
    """Récupère le hash du commit local si git est présent."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def check_for_updates() -> Dict[str, Any]:
    """Vérifie sur GitHub si une nouvelle version ou mise à jour est disponible."""
    current_commit = get_current_git_commit()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
    headers = {"User-Agent": "SuperVideoAI-Updater/1.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            latest_sha = data.get("sha", "")
            commit_msg = data.get("commit", {}).get("message", "Nouvelle mise à jour disponible")
            commit_date = data.get("commit", {}).get("author", {}).get("date", "")
            formatted_date = commit_date[:10] if commit_date else ""

            if current_commit:
                has_update = (current_commit != latest_sha) and not latest_sha.startswith(current_commit)
            else:
                has_update = False

            return {
                "success": True,
                "update_available": has_update,
                "current_version": current_commit[:7] if current_commit else "v1.0",
                "latest_version": latest_sha[:7] if latest_sha else "Dernière",
                "latest_message": commit_msg.split("\n")[0],
                "latest_date": formatted_date,
                "repo_url": f"https://github.com/{GITHUB_REPO}"
            }
        elif resp.status_code in (404, 409):
            return {
                "success": True,
                "update_available": False,
                "current_version": current_commit[:7] if current_commit else "v1.0",
                "latest_version": "Initial",
                "latest_message": "Dépôt initialisé sur GitHub",
                "latest_date": "",
                "repo_url": f"https://github.com/{GITHUB_REPO}"
            }
        else:
            return {
                "success": False,
                "error": f"GitHub a répondu avec le statut {resp.status_code}",
                "update_available": False
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "update_available": False
        }


def apply_update() -> Dict[str, Any]:
    """Applique la mise à jour (git pull ou téléchargement zip sécurisé)."""
    is_git = (PROJECT_ROOT / ".git").is_dir()

    if is_git:
        try:
            pull_res = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )
            if pull_res.returncode != 0:
                return {
                    "success": False,
                    "error": f"Échec de synchronisation Git : {pull_res.stderr or pull_res.stdout}"
                }

            # Mise à jour des dépendances si nécessaire
            pip_executable = PROJECT_ROOT / ".venv" / "bin" / "pip"
            if not pip_executable.exists():
                pip_executable = PROJECT_ROOT / ".venv" / "Scripts" / "pip.exe"

            if pip_executable.exists():
                subprocess.run(
                    [str(pip_executable), "install", "-r", "requirements.txt"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    timeout=120
                )

            new_commit = get_current_git_commit()
            return {
                "success": True,
                "message": "Mise à jour installée avec succès !",
                "version": new_commit[:7] if new_commit else "À jour",
                "restart_required": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    else:
        # Téléchargement direct de l'archive pour utilisateurs ZIP
        try:
            zip_url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"
            headers = {"User-Agent": "SuperVideoAI-Updater/1.0"}
            resp = requests.get(zip_url, headers=headers, timeout=60)
            if resp.status_code != 200:
                return {"success": False, "error": f"Téléchargement impossible (Code HTTP {resp.status_code})"}

            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                for member in z.infolist():
                    parts = Path(member.filename).parts
                    if len(parts) <= 1:
                        continue
                    rel_path = Path(*parts[1:])
                    # Préservation absolue des secrets et des créations utilisateur
                    if str(rel_path).startswith((".env", "outputs", "uploads", ".venv")):
                        continue

                    target_file = PROJECT_ROOT / rel_path
                    if member.is_dir():
                        target_file.mkdir(parents=True, exist_ok=True)
                    else:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(member) as src, open(target_file, "wb") as dst:
                            shutil.copyfileobj(src, dst)

            return {
                "success": True,
                "message": "Mise à jour des fichiers terminée avec succès !",
                "restart_required": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
