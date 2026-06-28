# CCDashboard

Dashboard local pour monitorer les sessions Claude Code (`~/.claude/projects`).

## Démarrage rapide (une ligne)

Prérequis : [`uv`](https://docs.astral.sh/uv/) et [Node.js/`npm`](https://nodejs.org/).

    git clone https://github.com/vincentmoreau-se/ccdashboard.git && cd ccdashboard && ./start.sh

`./start.sh` installe les dépendances des deux services puis démarre le **backend**
sur http://localhost:8000 et le **frontend** sur http://localhost:5173 (à ouvrir
dans le navigateur). `Ctrl+C` arrête les deux. Les sections ci-dessous détaillent
le lancement manuel service par service.

## Backend (FastAPI, uv)

    cd backend
    uv sync
    uv run uvicorn app.main:app --reload --port 8000

Tests : `cd backend && uv run pytest`

## Frontend (React + Vite)

    cd frontend
    npm install
    npm run dev    # http://localhost:5173

Build : `npm run build` · Tests : `npm test`

## Configuration (env, préfixe `CCDASH_`)

| Variable | Défaut | Rôle |
|---|---|---|
| `CCDASH_PROJECTS_DIR` | `~/.claude/projects` | dossier source |
| `CCDASH_CURRENCY` | `€` | devise affichée |
| `CCDASH_LIVE_ACTIVE_THRESHOLD_SECONDS` | `30` | seuil "session active" |
| `CCDASH_EXPORT_ENABLED` | `false` | active l'export central |
| `CCDASH_EXPORT_ENDPOINT` | — | URL POST du serveur central |
| `CCDASH_EXPORT_TOKEN` | — | bearer token |
| `CCDASH_EXPORT_INTERVAL_MINUTES` | `15` | période d'envoi |
| `CCDASH_EXPORT_INCLUDE_ENRICHED` | `false` | inclut titres/branche/version |
| `CCDASH_EXPORT_MACHINE_ID` / `_USER_ID` / `_INSTANCE_ID` | hostname / *dérivé* / `default` | identité source |

`user_id` est **dérivé** si non forcé via `CCDASH_EXPORT_USER_ID` :
`key:<sha256(ANTHROPIC_API_KEY de ~/.claude/settings.json)>` si la clé existe
(la clé brute n'est jamais transmise), sinon `anon:<uuid persisté localement>`.

## Prix

Éditer `pricing.json` (par million de tokens, par fournisseur/modèle). Un modèle
absent ⇒ coût marqué incomplet dans l'UI (jamais 0 silencieux).

## Export central (contrat de payload, projet futur)

`POST <endpoint>` avec `Authorization: Bearer <token>`, body :

    {
      "schema_version": 1,
      "source": {"machine_id": "...", "user_id": "...", "instance_id": "..."},
      "sent_at": "<iso>",
      "sessions": [ /* agrégats; enrichis si activés */ ],
      "projects": [ /* agrégats */ ]
    }

Envoi incrémental (curseur par session), agrégats seuls par défaut. Le SSE `/api/live`
bascule en reconnexion auto si la connexion tombe.
