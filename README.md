# ChocoBot - Maison Delcourt

Assistant IA qui conseille des coffrets de chocolats selon les goûts, le budget et les allergies des clients.
Développé en urgence pour Noël : à vous de le rendre conforme, sobre et fiable (voir le brief).

Le chatbot utilise un petit modèle de langage qui tourne **sur votre machine**, grâce à Ollama.

## 1. Première installation (à faire une seule fois)

### 1a. Installer Ollama et télécharger les modèles

1. Installer Ollama : https://ollama.com/download
   (ou, dans **PowerShell** : `irm https://ollama.com/install.ps1 | iex` ; Linux / Mac : `curl -fsSL https://ollama.com/install.sh | sh`)
2. **Fermer et rouvrir le terminal**, puis télécharger les modèles (quelques Go, prévoir environ 4 Go de mémoire libre) :
   ```
   ollama pull llama3.2:3b
   ollama pull llama3.2:1b
   ```
3. Vérifier : `ollama list` doit afficher les deux modèles.

### 1b. Créer l'environnement Python

Ouvrir un terminal **dans le dossier du projet** (celui qui contient `app.py`).

**Windows (Invite de commandes)**

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Windows (PowerShell)** : si l'activation est refusée (« l'exécution de scripts est désactivée »), tapez d'abord
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, ou utilisez l'Invite de commandes, ou n'activez pas le venv :
`.venv\Scripts\python -m pip install -r requirements.txt`.

**Linux / Mac**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Aucun fichier de configuration n'est nécessaire : le projet utilise Ollama et `llama3.2:3b` par défaut.

### 1c. Vérifier que tout fonctionne

```
python check_llm.py
```

Il affiche une réponse du modèle (la première prend plus de temps : le modèle se charge en mémoire).
S'il affiche une erreur, vérifiez qu'Ollama est lancé (icône de lama près de l'horloge) et que `ollama list` montre le modèle.

## 2. Lancer le projet (à chaque fois)

Dans le dossier du projet :

```
.venv\Scripts\activate          (Linux / Mac : source .venv/bin/activate)
uvicorn app:app --reload
```

Arrêter le serveur : Ctrl+C. Ollama doit rester lancé en arrière-plan.

## Où voir quoi

- **Le chatbot** : http://localhost:8000
- **Le back-office de la Maison Delcourt** (clients et conversations) : http://localhost:8000/admin
  Affiche un formulaire de connexion (pas de fenêtre native du navigateur) : identifiants par défaut
  `admin` / `delcourt` (changez-les, voir « Réglages facultatifs »).
- **La documentation de l'API** : http://localhost:8000/docs
- **La base de données** : le fichier `chocobot.db`, créé au premier message, dans le dossier où vous lancez `uvicorn`.
  Ouvrez-le avec [DB Browser for SQLite](https://sqlitebrowser.org/) (ou `sqlite3 chocobot.db`). Tables : `customers`, `messages`.
  Pour repartir de zéro, arrêtez le serveur et supprimez ce fichier.

## Mesurer

`python load_test.py 2` simule 2 conversations (10 messages), avec de nouvelles sessions à chaque lancement :
pratique pour mesurer l'état avant/après. Chaque message prend plusieurs secondes : commencez petit.

## Réglages facultatifs

### Identifiants du back-office (/admin)

Par défaut : `admin` / `delcourt`. La page `/admin` affiche toujours le formulaire de connexion : les identifiants
ne sont gardés qu'en mémoire dans l'onglet, donc dès qu'on quitte ou recharge la page, il faut se reconnecter
(aucune session, aucun cookie côté serveur).
Pour changer les identifiants, exportez des variables d'environnement avant de lancer `uvicorn`
(ou mettez-les dans un fichier `.env`) :

```
ADMIN_USER=delcourt
ADMIN_PASSWORD=mot-de-passe-solide
```

### Modèle LLM

Pour changer de modèle ou simuler des pannes, copiez `.env.example` en `.env` (une seule fois : le refaire écrase vos
réglages), décommentez les lignes voulues, puis relancez `uvicorn`.

## Fin de conversation

L'historique des messages d'une session est **supprimé de la base** quand la conversation se termine, c'est-à-dire :

- au clic sur « Nouvelle conversation » ;
- à la fermeture ou au rechargement de l'onglet.

Seules les conversations en cours apparaissent donc dans le back-office.

## Structure

- `app.py` : API FastAPI
- `chatbot.py` : logique de conversation
- `llm.py` : appel au modèle (Ollama)
- `db.py` : stockage SQLite
- `static/` : page de chat et back-office
- `data/catalog.json` : catalogue des coffrets
- `check_llm.py` : test de connexion au modèle
- `load_test.py` : série de messages pour mesurer
