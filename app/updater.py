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
VERSION_FILE = PROJECT_ROOT / ".version"


def get_current_git_commit() -> Optional[str]:
    """
    Récupère le hash de version locale :
    1. Depuis git rev-parse HEAD si git est disponible
    2. Depuis .git/refs/heads/main (lecture directe sans git installé)
    3. Depuis le fichier .version (utilisateurs sans git / archive ZIP)
    """
    if shutil.which("git") and (PROJECT_ROOT / ".git").is_dir():
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=4,
            )
            if res.returncode == 0 and res.stdout.strip():
                sha = res.stdout.strip()
                try:
                    VERSION_FILE.write_text(sha, encoding="utf-8")
                except Exception:
                    pass
                return sha
        except Exception:
            pass

    git_ref = PROJECT_ROOT / ".git" / "refs" / "heads" / "main"
    if git_ref.exists():
        try:
            sha = git_ref.read_text(encoding="utf-8").strip()
            if sha:
                return sha
        except Exception:
            pass

    if VERSION_FILE.exists():
        try:
            sha = VERSION_FILE.read_text(encoding="utf-8").strip()
            if sha:
                return sha
        except Exception:
            pass

    return None


def _find_pip_executable() -> Optional[Path]:
    candidates = [
        PROJECT_ROOT / ".runtime" / "python" / "Scripts" / "pip.exe",
        PROJECT_ROOT / ".runtime" / "python" / "bin" / "pip",
        PROJECT_ROOT / ".venv" / "Scripts" / "pip.exe",
        PROJECT_ROOT / ".venv" / "bin" / "pip",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
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

            if current_commit and latest_sha:
                has_update = (current_commit != latest_sha) and not latest_sha.startswith(current_commit)
            elif latest_sha and not current_commit:
                # Première initialisation du fichier .version
                try:
                    VERSION_FILE.write_text(latest_sha, encoding="utf-8")
                except Exception:
                    pass
                current_commit = latest_sha
                has_update = False
            else:
                has_update = False

            return {
                "success": True,
                "update_available": has_update,
                "current_version": current_commit[:7] if current_commit else "v1.0",
                "latest_version": latest_sha[:7] if latest_sha else "Dernière",
                "latest_message": commit_msg.split("\n")[0],
                "latest_date": formatted_date,
                "repo_url": f"https://github.com/{GITHUB_REPO}",
            }
        elif resp.status_code in (404, 409):
            return {
                "success": True,
                "update_available": False,
                "current_version": current_commit[:7] if current_commit else "v1.0",
                "latest_version": "Initial",
                "latest_message": "Dépôt initialisé sur GitHub",
                "latest_date": "",
                "repo_url": f"https://github.com/{GITHUB_REPO}",
            }
        else:
            return {
                "success": False,
                "error": f"GitHub a répondu avec le statut {resp.status_code}",
                "update_available": False,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "update_available": False,
        }


def apply_update() -> Dict[str, Any]:
    """Applique la mise à jour (via git pull si disponible, sinon téléchargement ZIP direct sans Git)."""
    has_git = bool(shutil.which("git")) and (PROJECT_ROOT / ".git").is_dir()

    if has_git:
        try:
            pull_res = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if pull_res.returncode == 0:
                pip_exec = _find_pip_executable()
                if pip_exec:
                    subprocess.run(
                        [str(pip_exec), "install", "-r", "requirements.txt"],
                        cwd=PROJECT_ROOT,
                        capture_output=True,
                        timeout=120,
                    )
                new_commit = get_current_git_commit()
                return {
                    "success": True,
                    "message": "Mise à jour installée avec succès !",
                    "version": new_commit[:7] if new_commit else "À jour",
                    "restart_required": True,
                }
        except Exception:
            pass

    # Mode universel sans Git (téléchargement ZIP direct depuis GitHub)
    try:
        zip_url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"
        headers = {"User-Agent": "SuperVideoAI-Updater/1.0"}
        resp = requests.get(zip_url, headers=headers, timeout=60)
        if resp.status_code != 200:
            return {"success": False, "error": f"Téléchargement impossible (Code HTTP {resp.status_code})"}

        protected_prefixes = (".env", "outputs", "uploads", ".venv", ".runtime", ".git")
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            for member in z.infolist():
                parts = Path(member.filename).parts
                if len(parts) <= 1:
                    continue
                rel_path = Path(*parts[1:])
                if not rel_path.parts or rel_path.parts[0] in protected_prefixes:
                    continue

                target_file = (PROJECT_ROOT / rel_path).resolve()
                if PROJECT_ROOT.resolve() not in target_file.parents:
                    continue

                if member.is_dir():
                    target_file.mkdir(parents=True, exist_ok=True)
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        with z.open(member) as src, open(target_file, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                    except PermissionError:
                        # Sur Windows, Super Video AI.exe peut être verrouillé pendant l'exécution
                        continue

        # Enregistrer le nouveau SHA dans .version
        try:
            commits_url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
            c_resp = requests.get(commits_url, headers=headers, timeout=10)
            if c_resp.status_code == 200:
                latest_sha = c_resp.json().get("sha", "")
                if latest_sha:
                    VERSION_FILE.write_text(latest_sha, encoding="utf-8")
        except Exception:
            pass

        pip_exec = _find_pip_executable()
        if pip_exec:
            subprocess.run(
                [str(pip_exec), "install", "-r", "requirements.txt"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                timeout=120,
            )

        return {
            "success": True,
            "message": "Mise à jour installée avec succès !",
            "restart_required": True,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
