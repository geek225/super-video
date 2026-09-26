#!/usr/bin/env bash
# ==============================================================================
# Lanceur en 1-Clic pour Super Video Studio sur macOS
# Double-cliquez sur ce fichier pour démarrer l'application locale
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "🎬 Démarrage de SUPER VIDEO AI - Local Studio..."
echo "📂 Dossier de travail : $DIR"
echo "=========================================================="

# Vérification de l'environnement virtuel
if [ ! -d ".venv" ]; then
    echo "⚙️  Création de l'environnement virtuel local..."
    python3 -m venv .venv
    echo "📦 Installation des dépendances..."
    "$DIR/.venv/bin/pip" install -r requirements.txt
fi

# Synchronisation automatique des mises à jour GitHub
if [ -d ".git" ]; then
    echo "🔄 Recherche de mises à jour sur GitHub..."
    git pull origin main --quiet 2>/dev/null || true
fi

# Création du fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# Fonction pour ouvrir le navigateur après un court délai
(
    sleep 2
    open "http://127.0.0.1:7860"
) &

echo "🚀 Lancement du serveur local sur http://127.0.0.1:7860..."
echo "💡 Votre navigateur va s'ouvrir automatiquement."
echo "🛑 Pour arrêter le serveur, fermez simplement cette fenêtre ou appuyez sur Ctrl+C."
echo "----------------------------------------------------------"

"$DIR/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 7860
