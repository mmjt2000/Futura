# 📘 Passation — FUTURA

**Version :** V4 · **Dernière mise à jour :** 28 octobre 2026
**Propriétaire :** Jean Thomas Montezuma Montreuil
**Public :** Maryse (14 ans, 3° secundaria, Mexique) et Laeticia (15 ans, 4° secundaria, Rép. Dominicaine)

> ⚠️ Ce document remplace les versions V2/V3. Elles décrivaient une architecture
> (missions.json, routers users/missions/progress/badges, seed.py) qui n'existe
> plus dans le code. Ce qui suit décrit le code réellement présent, vérifié par
> les tests décrits au §8.

---

## 1. Vision

Un mentorat technologique familial, aligné sur les programmes officiels (SEP,
MINERD) et les référentiels PISA. Chaque parcours suit un cycle en 6 temps :

| Étape | Contenu | Validation |
|---|---|---|
| 1. Contexte réel | Une accroche concrète + question de réflexion | Bouton « Continuar » |
| 2. Khan Academy | Lien vers le cours correspondant | Bouton « Terminé » |
| 3. Laboratoire | Un labo HTML interactif (curseur, graphique) | Ouverture + « Terminé » |
| 4. Carnet PISA | 4 questions (formular, emplear, interpretar, evaluar) | Les 4 réponses remplies |
| 5. Exercices PISA | 4 exercices de niveau 1 à 4 | 4 bonnes réponses |
| 6. Métacognition | Facile / difficile / à refaire | Complétion → XP |

---

## 2. État actuel

**Fonctionnel et testé (41 vérifications automatisées) :**

- 36 parcours (18 Maryse, 18 Laeticia) sur 18 champs disciplinaires.
- 40 laboratoires HTML autonomes, tous référencés et présents.
- Progression persistée étape par étape, reprise exacte à la reconnexion.
- Carnet PISA sauvegardé et relisible ; corrigé côté serveur pour les exercices.
- XP attribués une seule fois par parcours (915 XP disponibles au total).
- 5 badges proportionnels à l'avancement.
- 4 écrans : Inicio, Progreso, Hermanas, Laboratorio.
- Suivi du bien-être quotidien (sommeil, mouvement, humeur, énergie) — facultatif.
- PWA installable, service worker, icônes 192/512.

**Non couvert (assumé) :**

- Pas d'authentification : le profil se change en touchant l'avatar. Acceptable
  pour deux utilisatrices dans un cadre familial, à revoir si l'app devient publique.
- Pas de mode enseignant / tableau de bord parental.
- Pas de traduction : l'interface est en espagnol, le code et la doc en français.

---

## 3. Stack

- **Backend :** Python 3.12, FastAPI, SQLAlchemy 2, SQLite (Postgres possible via `DATABASE_URL`).
- **Frontend :** HTML/CSS/JS vanilla, aucune dépendance, `fetch` sur la même origine.
- **PWA :** manifest + service worker (cache d'abord pour les pages, réseau d'abord pour l'API).
- **Hébergement cible :** Render (plan gratuit).

---

## 4. Architecture réelle

```text
futura/
├── app/
│   ├── main.py              # FastAPI : montage des routers + static + /sw.js
│   ├── database.py          # SQLite local / Postgres si DATABASE_URL
│   ├── models.py            # 9 tables (voir §5)
│   ├── seed.py              # crée Maryse (1) et Laeticia (2) au démarrage
│   └── routers/
│       ├── parcours.py      # contenu, progression, carnet, exercices, complétion
│       ├── users.py         # profils, résumé, progression globale, sœur, badges
│       └── wellbeing.py     # suivi quotidien du bien-être
├── data/parcours.json       # LE CONTENU (36 parcours, source de vérité)
├── labos/                   # 40 labos HTML autonomes
├── static/
│   ├── index.html           # écran 1 : accueil + jauges + grille de parcours
│   ├── parcours_template.html  # le parcours à 6 étapes
│   ├── progreso.html        # écran 2 : XP, matières, badges, parcours finis
│   ├── hermanas.html        # écran 3 : comparaison avec la sœur
│   ├── laboratorio.html     # écran 4 : portfolio des carnets PISA
│   ├── theme.css            # design system (thème sombre/clair)
│   ├── app.js               # utilitaires partagés (API, thème, nav, profil)
│   ├── sw.js                # service worker
│   ├── manifest.json        # PWA
│   └── icons/               # icônes générées par scripts/make_icons.py
├── scripts/make_icons.py    # régénère les icônes PWA
├── tests/e2e_api.py         # tests end-to-end (urllib, sans dépendance)
├── render.yaml              # déploiement Render
├── requirements.txt
└── .gitignore
```

---

## 5. Modèle de données

| Table | Rôle | Utilisée |
|---|---|---|
| `users` | id, nom, pays, niveau, XP | ✅ |
| `parcours_progress` | 1 ligne par (utilisatrice, parcours) : 6 booléens d'étapes, `carnet_json`, `exercices_reussis`, `completed`, `xp_earned` | ✅ |
| `exercise_responses` | 1 ligne par (utilisatrice, exercice) : réponse, correction, nombre d'essais | ✅ |
| `wellbeing` | 1 ligne par (utilisatrice, jour) | ✅ |
| `missions`, `progress`, `badges`, `projects`, `parcours` | Ancien système V2, plus alimenté | ⚠️ mortes |

**Décision :** le contenu pédagogique reste dans `data/parcours.json`, jamais
dupliqué en base. On peut donc corriger une mission sans migration ; seule la
progression est en base.

**Carnet :** `carnet_json` stocke les 4 réponses sous la clé `process`, plus
`reflexion` (étape 1) et `_meta` (métacognition de l'étape 6).

---

## 6. API

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/users/` | Liste des profils |
| GET | `/api/users/{id}/summary` | XP, parcours terminés, badges, prochain badge |
| GET | `/api/users/{id}/progress` | Carte `{parcours_id: progression}` |
| GET | `/api/users/{id}/sisters` | Stats de l'autre sœur + son dernier parcours |
| GET | `/api/parcours/?target=Maryse` | Liste filtrée |
| GET | `/api/parcours/{id}` | Contenu complet d'un parcours |
| GET | `/api/parcours/{id}/progress?user_id=` | Étapes, carnet, exercices réussis |
| PATCH | `/api/parcours/{id}/etape` | Valide une étape (1 à 6) |
| PATCH | `/api/parcours/{id}/carnet` | Enregistre les réponses du carnet |
| POST | `/api/parcours/{id}/exercice` | Corrige une réponse ; révèle la solution après 3 essais |
| POST | `/api/parcours/{id}/complete` | Valide l'étape 6 et attribue les XP (idempotent) |
| GET/POST | `/api/wellbeing/{id}` | Bien-être du jour |
| GET | `/health` | Sonde Render |

Documentation interactive : `http://localhost:8000/docs`.

---

## 7. Gamification

- **XP :** 20 à 30 par parcours, 915 au total (18 parcours par fille).
- **Badges proportionnels** (dans `app/routers/users.py`) : Exploradora 0 %,
  Aprendiz 15 %, Creadora 35 %, Innovadora 60 %, Future Leader 85 %.
  Des seuils absolus (50/100/150/200 XP comme en V2) seraient atteints dès le
  troisième parcours et ne voudraient plus rien dire.
- **Correction :** côté serveur, normalisée (minuscules, accents retirés). Une
  réponse vide ne valide jamais. Après 3 essais, la réponse attendue est affichée.

---

## 8. Lancer en local

```powershell
cd C:\Dev\futura
.\.venv\Scripts\Activate.ps1        # ou py -3.12 -m venv .venv + pip install -r requirements.txt
uvicorn app.main:app --reload
```

→ http://localhost:8000 — la base `futura.db` se crée toute seule, avec Maryse et Laeticia.

### Tests

```powershell
# terminal 1 — base jetable, autre port
$env:DATABASE_URL = "sqlite:///./_test.db"
uvicorn app.main:app --port 8099

# terminal 2
python tests/e2e_api.py
```

Le script couvre les 8 domaines (profils, contenu, étapes, carnet, exercices,
XP, sœur/bien-être, pages/assets) et affiche `41/41 vérifications réussies`.
Il ne touche jamais `futura.db`.

---

## 9. Déploiement Render

1. Pousser le dossier sur GitHub (le `.gitignore` exclut `.venv` et `futura.db`).
2. Render → **New → Web Service** → lier le dépôt. `render.yaml` est détecté.
3. Commande de démarrage : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Vérifier `/health` puis l'URL publique.

**⚠️ Persistance.** En plan gratuit, le disque est éphémère : au réveil après
15 min d'inactivité, `futura.db` est recréée et **la progression est perdue**.
Deux options :

- **Postgres Render** (gratuit, recommandé) : créer une base, copier son URL
  interne dans la variable `DATABASE_URL` du service. `app/database.py` gère
  déjà la conversion `postgres://` → `postgresql://`. Ajouter `psycopg2-binary`
  aux dépendances.
- **Disque persistant** (payant) : monter le disque et déplacer la base dessus.

**Cache du service worker.** Après un déploiement, incrémenter `CACHE`
(`futura-v1` → `futura-v2`) dans `static/sw.js`, sinon les navigateurs servent
l'ancienne version des pages.

---

## 10. Points de vigilance

- **Encodage :** les fichiers JSON doivent rester en UTF-8 sans BOM. Éditer avec
  VS Code, pas avec PowerShell (`Out-File` ajoute un BOM).
- **`data/parcours.json` est la source de vérité du contenu.** Une faute de
  frappe dans un `expected_answer` rend un exercice invalide ; `tests/e2e_api.py`
  ne le détecte pas (il utilise la valeur du fichier). Relire les exercices à la main.
- **Une étape validée le reste** : pas de rétrogradation possible via l'API.
- **Pas d'authentification** : toute personne avec l'URL peut changer de profil.
- **Les tables `missions`/`progress`/`badges`/`projects`/`parcours`** sont mortes.
  Les supprimer de `models.py` demanderait une migration ; les laisser ne coûte rien.

---

## 11. Reste à faire

1. **Persistance Postgres** avant de donner l'URL aux filles (sinon progression perdue).
2. **Écran Bienestar** dédié : l'API existe (`/api/wellbeing`), l'écran se limite
   aujourd'hui à la carte de l'accueil.
3. **Défis entre sœurs** : `hermanas.html` compare les XP mais n'envoie pas de message.
4. **Vérification utilisateur** : faire jouer Maryse et Laeticia sur un parcours
   chacune et noter les frictions réelles.
5. **Contenu** : les 18 champs par fille sont couverts ; enrichir les exercices
   de niveau 4 (évaluation critique) qui restent les plus faibles.

---

## 12. Historique

| Version | Date | Contenu |
|---|---|---|
| V2 | 20 oct. 2026 | 20 missions, Pyodide, XP/badges — architecture `missions.json` |
| V3 | 22 oct. 2026 | 30 missions, carnet PISA, 16 labos — document jamais aligné sur le code |
| **V4** | **28 oct. 2026** | **Réécriture : 36 parcours, 40 labos, API complète, 4 écrans, PWA, tests, Render** |
markdown
# 📘 Passation — FUTURA

**Version :** V4.1 · **Dernière mise à jour :** 28 octobre 2026
**Propriétaire :** Jean Thomas Montezuma Montreuil
**Public :** Maryse (14 ans, 3° secundaria, Mexique) et Laeticia (15 ans, 4° secundaria, Rép. Dominicaine)

> ⚠️ Ce document remplace les versions V2/V3. Elles décrivaient une architecture
> (missions.json, routers users/missions/progress/badges, seed.py) qui n'existe
> plus dans le code. Ce qui suit décrit le code réellement présent, vérifié par
> les tests décrits au §8.

---

## 1. Vision

Un mentorat technologique familial, aligné sur les programmes officiels (SEP,
MINERD) et les référentiels PISA. Chaque parcours suit un cycle en 6 temps :

| Étape | Contenu | Validation |
|---|---|---|
| 1. Contexte réel | Une accroche concrète + question de réflexion | Bouton « Continuar » |
| 2. Khan Academy | Lien vers le cours correspondant | Bouton « Terminé » |
| 3. Laboratoire | Un labo HTML interactif (curseur, graphique) | Ouverture + « Terminé » |
| 4. Carnet PISA | 4 questions (formular, emplear, interpretar, evaluar) | Les 4 réponses remplies |
| 5. Exercices PISA | 4 exercices de niveau 1 à 4 | 4 bonnes réponses |
| 6. Métacognition | Facile / difficile / à refaire | Complétion → XP |

---

## 2. État actuel

**Fonctionnel et testé (41 vérifications automatisées) :**

- 36 parcours (18 Maryse, 18 Laeticia) sur 18 champs disciplinaires.
- 40 laboratoires HTML autonomes, tous référencés et présents.
- Progression persistée étape par étape, reprise exacte à la reconnexion.
- Carnet PISA sauvegardé et relisible ; corrigé côté serveur pour les exercices.
- XP attribués une seule fois par parcours (915 XP disponibles au total).
- 5 badges proportionnels à l'avancement.
- 4 écrans : Inicio, Progreso, Hermanas, Laboratorio.
- Suivi du bien-être quotidien (sommeil, mouvement, humeur, énergie) — facultatif.
- PWA installable, service worker, icônes 192/512.
- **Code source sauvegardé et hébergé sur GitHub.**

**Non couvert (assumé) :**

- Pas d'authentification : le profil se change en touchant l'avatar. Acceptable
  pour deux utilisatrices dans un cadre familial, à revoir si l'app devient publique.
- Pas de mode enseignant / tableau de bord parental.
- Pas de traduction : l'interface est en espagnol, le code et la doc en français.

---

## 3. Stack

- **Backend :** Python 3.12, FastAPI, SQLAlchemy 2, SQLite (Postgres possible via `DATABASE_URL`).
- **Frontend :** HTML/CSS/JS vanilla, aucune dépendance, `fetch` sur la même origine.
- **PWA :** manifest + service worker (cache d'abord pour les pages, réseau d'abord pour l'API).
- **Hébergement cible :** Render (plan gratuit).
- **Versioning :** Git (dépôt local et distant sur GitHub : `mmjt2000/Futura`).

---

## 4. Architecture réelle

```text
futura/
├── app/
│   ├── main.py              # FastAPI : montage des routers + static + /sw.js
│   ├── database.py          # SQLite local / Postgres si DATABASE_URL
│   ├── models.py            # 9 tables (voir §5)
│   ├── seed.py              # crée Maryse (1) et Laeticia (2) au démarrage
│   └── routers/
│       ├── parcours.py      # contenu, progression, carnet, exercices, complétion
│       ├── users.py         # profils, résumé, progression globale, sœur, badges
│       └── wellbeing.py     # suivi quotidien du bien-être
├── data/parcours.json       # LE CONTENU (36 parcours, source de vérité)
├── labos/                   # 40 labos HTML autonomes
├── static/
│   ├── index.html           # écran 1 : accueil + jauges + grille de parcours
│   ├── parcours_template.html  # le parcours à 6 étapes
│   ├── progreso.html        # écran 2 : XP, matières, badges, parcours finis
│   ├── hermanas.html        # écran 3 : comparaison avec la sœur
│   ├── laboratorio.html     # écran 4 : portfolio des carnets PISA
│   ├── theme.css            # design system (thème sombre/clair)
│   ├── app.js               # utilitaires partagés (API, thème, nav, profil)
│   ├── sw.js                # service worker
│   ├── manifest.json        # PWA
│   └── icons/               # icônes générées par scripts/make_icons.py
├── scripts/make_icons.py    # régénère les icônes PWA
├── tests/e2e_api.py         # tests end-to-end (urllib, sans dépendance)
├── render.yaml              # déploiement Render
├── requirements.txt
├── .gitignore               # exclut .venv et futura.db
└── PASSATION.md             # ce document
5. Modèle de données
Table	Rôle	Utilisée
users	id, nom, pays, niveau, XP	✅
parcours_progress	1 ligne par (utilisatrice, parcours) : 6 booléens d'étapes, carnet_json, exercices_reussis, completed, xp_earned	✅
exercise_responses	1 ligne par (utilisatrice, exercice) : réponse, correction, nombre d'essais	✅
wellbeing	1 ligne par (utilisatrice, jour)	✅
missions, progress, badges, projects, parcours	Ancien système V2, plus alimenté	⚠️ mortes
Décision : le contenu pédagogique reste dans data/parcours.json, jamais
dupliqué en base. On peut donc corriger une mission sans migration ; seule la
progression est en base.

Carnet : carnet_json stocke les 4 réponses sous la clé process, plus
reflexion (étape 1) et _meta (métacognition de l'étape 6).

6. API
Méthode	Route	Rôle
GET	/api/users/	Liste des profils
GET	/api/users/{id}/summary	XP, parcours terminés, badges, prochain badge
GET	/api/users/{id}/progress	Carte {parcours_id: progression}
GET	/api/users/{id}/sisters	Stats de l'autre sœur + son dernier parcours
GET	/api/parcours/?target=Maryse	Liste filtrée
GET	/api/parcours/{id}	Contenu complet d'un parcours
GET	/api/parcours/{id}/progress?user_id=	Étapes, carnet, exercices réussis
PATCH	/api/parcours/{id}/etape	Valide une étape (1 à 6)
PATCH	/api/parcours/{id}/carnet	Enregistre les réponses du carnet
POST	/api/parcours/{id}/exercice	Corrige une réponse ; révèle la solution après 3 essais
POST	/api/parcours/{id}/complete	Valide l'étape 6 et attribue les XP (idempotent)
GET/POST	/api/wellbeing/{id}	Bien-être du jour
GET	/health	Sonde Render
Documentation interactive : http://localhost:8000/docs.

7. Gamification
XP : 20 à 30 par parcours, 915 au total (18 parcours par fille).

Badges proportionnels (dans app/routers/users.py) : Exploradora 0 %,
Aprendiz 15 %, Creadora 35 %, Innovadora 60 %, Future Leader 85 %.
Des seuils absolus (50/100/150/200 XP comme en V2) seraient atteints dès le
troisième parcours et ne voudraient plus rien dire.

Correction : côté serveur, normalisée (minuscules, accents retirés). Une
réponse vide ne valide jamais. Après 3 essais, la réponse attendue est affichée.

8. Lancer en local et Versioning
powershell
cd C:\Dev\futura
.\.venv\Scripts\Activate.ps1        # ou py -3.12 -m venv .venv + pip install -r requirements.txt
uvicorn app.main:app --reload
→ http://localhost:8000 — la base futura.db se crée toute seule, avec Maryse et Laeticia.

Tests
powershell
# terminal 1 — base jetable, autre port
$env:DATABASE_URL = "sqlite:///./_test.db"
uvicorn app.main:app --port 8099

# terminal 2
python tests/e2e_api.py
Le script couvre les 8 domaines (profils, contenu, étapes, carnet, exercices,
XP, sœur/bien-être, pages/assets) et affiche 41/41 vérifications réussies.
Il ne touche jamais futura.db.

Sauvegarde Git
Le projet est initialisé avec Git et lié à GitHub (https://github.com/mmjt2000/Futura.git).
Pour sauvegarder les modifications après une session de développement :

bash
git add .
git commit -m "Description de la modification"
git push
9. Déploiement Render
Pousser le dossier sur GitHub (le .gitignore exclut .venv et futura.db).

Render → New → Web Service → lier le dépôt. render.yaml est détecté.

Commande de démarrage : uvicorn app.main:app --host 0.0.0.0 --port $PORT.

Vérifier /health puis l'URL publique.

⚠️ Persistance. En plan gratuit, le disque est éphémère : au réveil après
15 min d'inactivité, futura.db est recréée et la progression est perdue.
Deux options :

Postgres Render (gratuit, recommandé) : créer une base, copier son URL
interne dans la variable DATABASE_URL du service. app/database.py gère
déjà la conversion postgres:// → postgresql://. Ajouter psycopg2-binary
aux dépendances.

Disque persistant (payant) : monter le disque et déplacer la base dessus.

Cache du service worker. Après un déploiement, incrémenter CACHE
(futura-v1 → futura-v2) dans static/sw.js, sinon les navigateurs servent
l'ancienne version des pages.

10. Points de vigilance
Encodage : les fichiers JSON doivent rester en UTF-8 sans BOM. Éditer avec
VS Code, pas avec PowerShell (Out-File ajoute un BOM).

data/parcours.json est la source de vérité du contenu. Une faute de
frappe dans un expected_answer rend un exercice invalide ; tests/e2e_api.py
ne le détecte pas (il utilise la valeur du fichier). Relire les exercices à la main.

Une étape validée le reste : pas de rétrogradation possible via l'API.

Pas d'authentification : toute personne avec l'URL peut changer de profil.

Les tables missions/progress/badges/projects/parcours sont mortes.
Les supprimer de models.py demanderait une migration ; les laisser ne coûte rien.

11. Reste à faire
Persistance Postgres avant de donner l'URL aux filles (sinon progression perdue).

Écran Bienestar dédié : l'API existe (/api/wellbeing), l'écran se limite
aujourd'hui à la carte de l'accueil.

Défis entre sœurs : hermanas.html compare les XP mais n'envoie pas de message.

Vérification utilisateur : faire jouer Maryse et Laeticia sur un parcours
chacune et noter les frictions réelles.

Contenu : les 18 champs par fille sont couverts ; enrichir les exercices
de niveau 4 (évaluation critique) qui restent les plus faibles.

12. Historique
Version	Date	Contenu
V2	20 oct. 2026	20 missions, Pyodide, XP/badges — architecture missions.json
V3	22 oct. 2026	30 missions, carnet PISA, 16 labos — document jamais aligné sur le code
V4	28 oct. 2026	Réécriture : 36 parcours, 40 labos, API complète, 4 écrans, PWA, tests, Render
V4.1	28 oct. 2026	Ajout de la section Git/GitHub (§8), mise à jour de l'état (§2) et de l'historique.
text

***

### 🚀 Ce qu'il te reste à faire pour finaliser cette mise à jour :

Puisque tu as modifié un fichier, il faut le sauvegarder sur GitHub. Dans ton terminal PowerShell (assure-toi d'être dans `C:\Dev\Futura`), tape ces trois petites commandes :

1. `git add PASSATION.md`
2. `git commit -m "Mise à jour de la documentation avec la configuration Git et GitHub"`
3. `git push`

Et voilà ! Ton projet est non seulement fonctionnel, mais en plus il est parfaitement documenté pour le futur. Tu as fait un travail de chef d'équipe !
