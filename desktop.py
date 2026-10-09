import os
import sys
import time
import shutil
import socket
import threading
import subprocess
import webbrowser
import http.client
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from app.main import app
from app.config import OUTPUTS_DIR

HOST = "127.0.0.1"
DEFAULT_PORT = 7860


def _sanitize_filename(filename: str) -> Path:
    """Valide strictement que le fichier appartient au dossier outputs/ (anti Path Traversal)."""
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."} or "/" in filename or "\\" in filename:
        raise ValueError("Nom de fichier invalide.")
    target = (OUTPUTS_DIR / safe_name).resolve()
    if OUTPUTS_DIR.resolve() not in target.parents:
        raise ValueError("Accès non autorisé en dehors du dossier outputs.")
    return target


class DesktopAPI:
    """Pont natif Python <-> Interface Desktop (PyWebView)."""

    def __init__(self) -> None:
        self._window: Optional[Any] = None

    def set_window(self, window: Any) -> None:
        self._window = window

    def is_desktop(self) -> bool:
        return True

    def save_video(self, filename: str) -> Dict[str, Any]:
        """Ouvre une vraie boîte de dialogue native 'Enregistrer sous...' sur Mac et Windows."""
        try:
            source_file = _sanitize_filename(filename)
            if not source_file.exists():
                return {"success": False, "error": "Fichier vidéo introuvable."}

            if self._window is None:
                return {"success": False, "error": "Fenêtre principale non initialisée."}

            import webview

            downloads_dir = Path.home() / "Downloads"
            if not downloads_dir.exists():
                downloads_dir = Path.home()

            dialog_type = getattr(webview, "SAVE_DIALOG", 30)
            result = self._window.create_file_dialog(
                dialog_type,
                directory=str(downloads_dir),
                save_filename=source_file.name,
                file_types=("Vidéo MP4 (*.mp4)", "Tous les fichiers (*.*)"),
            )

            if not result:
                return {"success": False, "cancelled": True}

            dest_path_str = result[0] if isinstance(result, (list, tuple)) else str(result)
            if not dest_path_str:
                return {"success": False, "cancelled": True}

            dest_path = Path(dest_path_str)
            if dest_path.suffix.lower() != ".mp4":
                dest_path = dest_path.with_suffix(".mp4")

            shutil.copy2(source_file, dest_path)
            return {"success": True, "saved_path": str(dest_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reveal_in_folder(self, filename: str) -> Dict[str, Any]:
        """Ouvre le Finder (macOS) ou l'Explorateur Windows directement sur la vidéo."""
        try:
            source_file = _sanitize_filename(filename)
            target_to_show = source_file if source_file.exists() else OUTPUTS_DIR.resolve()

            if sys.platform == "darwin":
                if source_file.exists():
                    subprocess.run(["open", "-R", str(target_to_show)], check=False)
                else:
                    subprocess.run(["open", str(OUTPUTS_DIR.resolve())], check=False)
            elif sys.platform == "win32":
                if source_file.exists():
                    subprocess.run(["explorer.exe", f"/select,{str(target_to_show)}"], check=False)
                else:
                    subprocess.run(["explorer.exe", str(OUTPUTS_DIR.resolve())], check=False)
            else:
                subprocess.run(["xdg-open", str(OUTPUTS_DIR.resolve())], check=False)

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


def _is_server_responding(port: int) -> bool:
    conn: Optional[http.client.HTTPConnection] = None
    try:
        conn = http.client.HTTPConnection(HOST, int(port), timeout=0.6)
        conn.request("GET", "/api/settings")
        resp = conn.getresponse()
        return resp.status == 200
    except Exception:
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, port)) == 0


def _find_available_port(start_port: int = DEFAULT_PORT) -> int:
    if _is_server_responding(start_port):
        return start_port
    if not _is_port_in_use(start_port):
        return start_port
    for p in range(start_port + 1, start_port + 20):
        if not _is_port_in_use(p):
            return p
    return start_port


def main() -> None:
    port = _find_available_port(DEFAULT_PORT)
    server_url = f"http://{HOST}:{port}"
    uvicorn_server: Optional[uvicorn.Server] = None

    if not _is_server_responding(port):
        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=port,
            log_level="warning",
            access_log=False,
        )
        uvicorn_server = uvicorn.Server(config)
        server_thread = threading.Thread(target=uvicorn_server.run, daemon=True)
        server_thread.start()

        # Attendre que le serveur local soit prêt (max 8 secondes)
        for _ in range(40):
            if _is_server_responding(port):
                break
            time.sleep(0.2)

    try:
        import webview

        api = DesktopAPI()
        window = webview.create_window(
            title="Super Video AI — Studio Motion & Vidéo",
            url=server_url,
            width=1440,
            height=900,
            min_size=(1024, 700),
            background_color="#05050A",
            text_select=False,
            js_api=api,
        )
        api.set_window(window)
        webview.start(debug=False)
    except Exception as exc:
        print(f"[INFO] Mode fenêtre WebView indisponible ({exc}), ouverture en mode navigateur...")
        webbrowser.open(server_url)
        if uvicorn_server is not None:
            try:
                while not uvicorn_server.should_exit:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    finally:
        if uvicorn_server is not None:
            uvicorn_server.should_exit = True


if __name__ == "__main__":
    main()
