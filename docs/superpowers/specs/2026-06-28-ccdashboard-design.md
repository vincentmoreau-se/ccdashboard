# CCDashboard — Design

**Date:** 2026-06-28
**Statut:** Validé (design), prêt pour le plan d'implémentation

## Objectif

Dashboard web généraliste pour **monitorer et comprendre** le fonctionnement
des sessions Claude Code locales. Il combine quatre dimensions : vue d'ensemble
des coûts/tokens, activité & productivité, exploration détaillée d'une session,
et suivi en temps réel des sessions actives.

Source de données : les fichiers `~/.claude/projects/<projet>/<session>.jsonl`
écrits par Claude Code sur cette machine (WSL).

## Décisions clés

| Sujet | Décision |
|---|---|
| Périmètre | Dashboard généraliste : Overview + Projets + Explorateur de session + Live |
| Mode | Historique complet **et** temps réel (sessions actives en direct) |
| Hébergement | Local sur la machine WSL (accès direct aux fichiers) |
| Stack | Backend **FastAPI** (Python, géré avec `uv`) + frontend **React + Vite + TypeScript** |
| Coût | Coût monétaire estimé, table de prix configurable par modèle/fournisseur |
| Cache/perf | Cache **en mémoire** (clé = chemin + mtime), watcher fichiers pour le live |
| Export central | Option **désactivée par défaut** : push périodique d'agrégats vers un serveur central (projet futur) |

## 1. Architecture

```
ccdashboard/
├── backend/                    # FastAPI (Python, géré avec uv)
│   ├── app/
│   │   ├── main.py             # app FastAPI + routes
│   │   ├── parser.py           # lecture & parsing des .jsonl
│   │   ├── store.py            # cache mémoire (clé = chemin+mtime)
│   │   ├── metrics.py          # agrégations (overview, projets, séries temporelles)
│   │   ├── pricing.py          # calcul coût à partir de pricing.json
│   │   ├── watcher.py          # surveillance fichiers + flux SSE live
│   │   ├── exporter.py         # construction payload + curseur + envoi central
│   │   ├── models.py           # schémas Pydantic (réponses API)
│   │   └── config.py           # chemins, constantes, configuration
│   ├── tests/                  # pytest + fixtures .jsonl
│   └── pyproject.toml
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/              # Overview, Projects, ProjectDetail, Session, Live
│   │   ├── components/         # cartes KPI, graphes, timeline…
│   │   ├── api/                # client REST + abonnement SSE
│   │   └── lib/                # formatage tokens/coûts/dates
│   └── package.json
├── pricing.json                # table de prix configurable par modèle/fournisseur
└── README.md
```

**Flux de données :**
- Historique : Frontend React → API REST (FastAPI) → `parser` lit
  `~/.claude/projects/` et met en cache (`store`) → `metrics` agrège →
  `pricing` chiffre → réponse JSON.
- Temps réel : la page Live s'abonne à un flux **SSE** alimenté par le
  `watcher`, qui détecte les fichiers modifiés et pousse les nouvelles lignes.

## 2. Modèle de données

Le parser transforme chaque ligne `.jsonl` pertinente en `MessageRecord`, puis
on dérive `SessionSummary` (par fichier) et `ProjectSummary` (par dossier), plus
des agrégats temporels pour les graphes.

### `MessageRecord` (une ligne pertinente)
- `uuid`, `parent_uuid`, `timestamp`, `type` (user / assistant / system / tool_result)
- `model` (si assistant), `git_branch`, `cwd`, `cc_version`
- `usage` : `input`, `output`, `cache_creation` (5m + 1h), `cache_read`,
  `web_search`, `web_fetch`
- `tools` : liste des outils appelés (nom + statut éventuel)
- `content_kind` : `text` / `thinking` / `tool_use` / `tool_result`
  (le verbatim n'est pas stocké par défaut ; chargeable à la demande)

### `SessionSummary` (un fichier `.jsonl`)
- `session_id`, `project` (nom de dossier + cwd réel), `file_path`, `ai_title`
- `started_at`, `ended_at`, `duration`, `is_active` (modifié récemment)
- `model(s)`, `git_branch`, `cc_version`, `provider` (anthropic / bedrock, best-effort)
- Totaux : `message_count`, tokens par catégorie, **coût estimé**,
  répartition des outils (Bash, Edit, Read…)

### `ProjectSummary` (un dossier)
- `name`, `path`, `session_count`, totaux tokens + coût, `last_activity`,
  modèles utilisés

### Agrégats temporels
- Séries par jour/semaine : sessions, tokens (par catégorie), coût ;
  filtrables par projet/modèle.

### Explorateur de session
- Parsing à la demande du fichier ciblé → liste de `MessageRecord` (timeline).
- Contenu complet d'un message chargeable à la demande pour inspection.

## 3. Calcul du coût & fournisseur

Table de prix éditable à la main dans `pricing.json` (prix **par million de
tokens**), structurée par fournisseur puis par modèle :

```jsonc
{
  "anthropic": {
    "claude-opus-4-8":   { "input": 5.0, "output": 25.0,
                           "cache_write_5m": 6.25, "cache_write_1h": 10.0,
                           "cache_read": 0.5 },
    "claude-sonnet-4-6": { "input": 3.0, "output": 15.0, "cache_write_5m": 3.75,
                           "cache_write_1h": 6.0, "cache_read": 0.3 },
    "claude-haiku-4-5":  { "input": 1.0, "output": 5.0, "cache_write_5m": 1.25,
                           "cache_write_1h": 2.0, "cache_read": 0.1 }
  },
  "bedrock": {
    "claude-opus-4-8":   { "input": 5.0, "output": 25.0, "cache_write_5m": 6.25,
                           "cache_write_1h": 10.0, "cache_read": 0.5 }
  }
}
```

> Les valeurs sont pré-remplies à titre de référence et **ajustables par
> l'utilisateur** — c'est lui qui a la main sur les chiffres exacts.

**Formule (par message), tout ramené à /1M tokens :**
```
coût = input·p_in + output·p_out
     + cache_creation_5m·p_cw5m + cache_creation_1h·p_cw1h
     + cache_read·p_cr
```
Coût session = somme des messages ; coût projet = somme des sessions.

**Détection du fournisseur (best-effort) :**
- Indices dans le `.jsonl` : préfixe modèle (`us.anthropic.…` ⇒ Bedrock),
  `entrypoint`/config éventuels.
- Indéterminé → fournisseur **par défaut configurable** (ex. `anthropic`).
- **Modèle absent de la table** → coût marqué `inconnu` et **remonté dans l'UI**
  (badge), jamais silencieusement à 0.

**Affichage :** devise configurable (€ / $) ; tokens toujours affichés à côté du
coût pour la transparence.

## 4. Temps réel (Live)

- **Session active** : fichier `.jsonl` modifié dans les *N* dernières secondes
  (seuil configurable, défaut ~30 s).
- **Mécanisme** : le `watcher` (watchdog) observe `~/.claude/projects/`. À chaque
  modification d'un fichier actif, il lit **uniquement les nouvelles lignes**
  (suivi d'offset) et pousse un événement sur un flux **SSE**.
- **Frontend** : la page Live s'abonne au SSE → mise à jour en direct (tokens
  cumulés, dernier outil appelé, dernier message, modèle, durée). Repli en
  polling si le SSE tombe.
- Le reste de l'app utilise REST ; la page Live est la seule consommatrice du
  SSE.

## 5. Gestion d'erreurs

- **Ligne JSONL corrompue** → ignorée + comptée (compteur « lignes ignorées »
  consultable pour debug).
- **Champs `usage` manquants** → traités comme 0 (pas de crash).
- **Modèle hors table de prix** → coût `inconnu` + badge UI.
- **Fichier illisible / permission** → session marquée en erreur, le reste
  continue de charger.
- **Projet/fichier vide** → ignoré proprement.
- **SSE interrompu** → reconnexion auto côté frontend + repli polling.

## 6. Tests

- **Backend (priorité)** avec **pytest** + fixture `.jsonl` représentative :
  - `parser` : lignes valides/corrompues, champs manquants, types variés
  - `metrics` : agrégations session/projet/temporelles
  - `pricing` : calcul de coût, fournisseur, modèle inconnu
  - `exporter` : construction du payload, curseur incrémental, échec d'envoi
- **Frontend** : tests de fumée légers sur les composants clés (rendu cartes /
  graphes avec données mockées). La logique métier vit côté backend → tests y
  sont concentrés.

## 7. Export vers serveur centralisé (optionnel, projet futur)

**Désactivé par défaut.** Activé via config (`export.enabled = true`). Le serveur
central fera l'objet d'un projet ultérieur ; ici on fournit l'export + le contrat
de payload.

**Données envoyées** : agrégats uniquement par défaut — `SessionSummary` /
`ProjectSummary` **sans contenu de message ni titre** (tokens, coût, modèle,
durée, nb messages, répartition d'outils, timestamps). Champs enrichis
(`ai_title`, `git_branch`, `cc_version`) inclus **seulement si**
`export.include_enriched = true`.

**Identité (config)** : `machine_id` (défaut = hostname), `user_id`,
`instance_id` stable — joints à chaque payload.

**Déclenchement** : tâche de fond **périodique** (intervalle configurable,
ex. 15 min) tant que le dashboard tourne. Envoi **incrémental** : curseur
(dernier timestamp/offset poussé par session) → on ne renvoie que le nouveau.
Le curseur n'avance qu'en cas de succès.

**Transport** : `POST` HTTPS vers `export.endpoint`, en-tête
`Authorization: Bearer <token>`. Payload JSON **versionné** :

```jsonc
{
  "schema_version": 1,
  "source": { "machine_id": "...", "user_id": "...", "instance_id": "..." },
  "sent_at": "2026-06-28T...Z",
  "sessions": [ /* agrégats, + champs enrichis si activés */ ],
  "projects": [ /* agrégats */ ]
}
```

**Robustesse** : endpoint **mockable** (le serveur central n'existe pas encore →
tests contre un faux serveur). Échec d'envoi = log + nouvelle tentative au cycle
suivant, sans perte. Composant isolé : `backend/app/exporter.py`.

## Configuration (synthèse)

Toute la configuration est centralisée (`backend/app/config.py` + fichier/env) :
- `claude_projects_dir` (défaut `~/.claude/projects`)
- `currency` (€/$), chemin de `pricing.json`, fournisseur par défaut
- `live.active_threshold_seconds` (défaut ~30)
- `export.enabled` (défaut `false`), `export.endpoint`, `export.token`,
  `export.interval_minutes`, `export.include_enriched` (défaut `false`),
  `export.machine_id`, `export.user_id`, `export.instance_id`

## Hors périmètre (YAGNI)

- Cache persistant SQLite (structure prévue pour l'ajouter plus tard si besoin).
- Conteneurisation / déploiement NAS (local uniquement pour l'instant).
- Le dashboard centralisé lui-même (projet futur ; seul l'export est livré ici).
- Édition de la table de prix via l'UI (édition manuelle de `pricing.json`).
