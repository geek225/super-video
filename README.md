# 🎬 Super Video AI - Studio Local Professionnel

Mini-logiciel local complet pour animer des images et concevoir du **Motion Design d'affiches** ou de la **vidéo cinématographique** fluide grâce à l'IA (moteur de rendu inclus sans frais).

---

## 📦 1. Partager le projet à un collaborateur

Pour transmettre ce dossier à quelqu'un d'autre :
1. **Ce qu'il faut envoyer** : Tout le dossier `super video/` **SAUF** :
   - Le dossier `.venv/` (l'environnement sera automatiquement recréé sur sa machine).
   - Le fichier `.env` (pour ne pas partager votre clé privée si elle doit rester personnelle).
2. **Astuce rapide** : Compressez le dossier en fichier `.zip` (en excluant `.venv`).

---

## 🚀 2. Démarrage sur la machine locale du destinataire

### Pré-requis unique
- Avoir **Python 3.10+** installé sur la machine ([python.org](https://www.python.org/)).
  *(Sur Windows, bien cocher "Add Python to PATH" lors de l'installation).*

---

### Option A : Sur Mac (macOS)
1. Double-cliquez simplement sur **`lancer.command`**.
2. *Note macOS :* Si macOS affiche "Fichier non approuvé" ou refuse l'exécution au premier lancement (sécurité Gatekeeper), faites simplement :
   - Clic-droit sur `lancer.command` > **Ouvrir** > confirmer **Ouvrir**.
   - Ou ouvrez le Terminal dans le dossier et tapez :
     ```bash
     chmod +x lancer.command start.sh
     ./lancer.command
     ```
3. Le script configure automatiquement l'environnement virtuel, installe les dépendances et ouvre l'interface sur `http://127.0.0.1:7860`.

---

### Option B : Sur Windows
1. Double-cliquez simplement sur **`lancer.bat`**.
2. Le script configure automatiquement l'environnement `.venv`, installe les dépendances et ouvre votre navigateur par défaut sur `http://127.0.0.1:7860`.

---

### Option C : Sur Linux ou Terminal universel
```bash
chmod +x start.sh
./start.sh
```

---

## 🔑 3. Configuration de la Clé Studio

Une fois l'interface ouverte dans le navigateur :
1. Cliquez sur le bouton **"Clé Studio"** en haut à droite.
2. Collez votre clé d'activation Studio (commençant par `sk-...`).
3. Cliquez sur **"Enregistrer la clé Studio"**.
4. La clé est stockée localement dans le fichier `.env` sur la machine.

---

## 🎨 4. Fonctionnalités Principales

- **Mode Motion Design Affiche (Anti-déformation)** :
  - **Maintien Personnage 2.5D** : Verrouille strictement les visages, corps et objets sans morphing.
  - **Effets d'ambiance visuelle** : Reflets dorés / trophée, confettis festifs, projecteurs, fumée volumétrique, particules lumineuses.
  - **Mouvements Caméra 2.5D** : Push-in lent, parallaxe 3D, travelling latéral, plan fixe.
- **Mode Vidéo Libre Cinéma** : Prompting libre pour scènes d'action et création cinématique.
- **Cadrage Automatique Intelligent** : Détecte le ratio d'origine (1:1, 3:4, 9:16, 16:9) pour éviter tout rognage de tête ou de trophée.
- **Sauvegarde Locale Instantanée** : Les vidéos générées sont automatiquement sauvegardées au format `.mp4` dans le dossier local `outputs/`.
