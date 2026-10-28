"""
Parcours PISA : contenu, progression par étape, carnet, exercices, complétion.

Le contenu (36 parcours) vit dans data/parcours.json. La base ne stocke que la
progression, ce qui rend l'édition du contenu indépendante des migrations.
"""
import json
import os
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/parcours", tags=["parcours"])

PARCOURS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "parcours.json")

ETAPES = {
    1: "etape1_contexte",
    2: "etape2_khan",
    3: "etape3_labo",
    4: "etape4_carnet",
    5: "etape5_exercices",
    6: "etape6_metacognition",
}


# ---------------------------------------------------------------------------
#  Contenu
# ---------------------------------------------------------------------------
def load_parcours_data() -> dict:
    if not os.path.exists(PARCOURS_FILE):
        raise HTTPException(status_code=500, detail="Fichier parcours.json introuvable")
    with open(PARCOURS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_parcours(parcours_id: str) -> dict:
    for p in load_parcours_data().get("parcours", []):
        if p["id"] == parcours_id:
            return p
    raise HTTPException(status_code=404, detail="Parcours introuvable")


# ---------------------------------------------------------------------------
#  Progression
# ---------------------------------------------------------------------------
def get_or_create_progress(db: Session, user_id: int, parcours_id: str) -> models.ParcoursProgress:
    progress = (
        db.query(models.ParcoursProgress)
        .filter(
            models.ParcoursProgress.user_id == user_id,
            models.ParcoursProgress.parcours_id == parcours_id,
        )
        .first()
    )
    if not progress:
        progress = models.ParcoursProgress(user_id=user_id, parcours_id=parcours_id)
        db.add(progress)
        db.flush()
    return progress


def _completed_etapes(progress: models.ParcoursProgress) -> list[int]:
    return [n for n, field in ETAPES.items() if getattr(progress, field)]


def _payload(progress: models.ParcoursProgress) -> dict:
    carnet = {}
    if progress.carnet_json:
        try:
            carnet = json.loads(progress.carnet_json)
        except (ValueError, TypeError):
            carnet = {}
    exercices = []
    if progress.exercices_reussis:
        try:
            exercices = json.loads(progress.exercices_reussis)
        except (ValueError, TypeError):
            exercices = []

    return {
        "etapes": _completed_etapes(progress),
        "completed": bool(progress.completed),
        "xp_earned": progress.xp_earned or 0,
        "carnet": {k: v for k, v in carnet.items() if not k.startswith("_")},
        "metacognition": carnet.get("_meta", {}),
        "exercices_reussis": exercices,
    }


# ---------------------------------------------------------------------------
#  Correction des réponses
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .;:!?")


def answer_matches(response: str, expected: str) -> bool:
    """Tolérant sur la forme, strict sur le fond.

    La comparaison par sous-chaîne est bornée à 2 caractères minimum pour
    éviter qu'une réponse vide ou d'une lettre valide un exercice.
    """
    a, b = _normalize(response), _normalize(expected)
    if not a or not b:
        return False
    if a == b:
        return True
    if len(b) >= 2 and b in a:
        return True
    if len(a) >= 2 and a in b:
        return True
    return False


# ---------------------------------------------------------------------------
#  Routes
# ---------------------------------------------------------------------------
@router.get("/")
def list_parcours(target: str = None):
    parcours = load_parcours_data().get("parcours", [])
    if target:
        parcours = [p for p in parcours if p["target_user"].lower() == target.lower()]
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "field": p["field"],
            "target_user": p["target_user"],
            "xp_reward": p["xp_reward"],
            "prerequisite": p.get("prerequisite"),
        }
        for p in parcours
    ]


@router.get("/{parcours_id}")
def get_parcours(parcours_id: str):
    return find_parcours(parcours_id)


@router.get("/{parcours_id}/progress")
def get_progress(parcours_id: str, user_id: int = 1, db: Session = Depends(get_db)):
    find_parcours(parcours_id)
    progress = (
        db.query(models.ParcoursProgress)
        .filter(
            models.ParcoursProgress.user_id == user_id,
            models.ParcoursProgress.parcours_id == parcours_id,
        )
        .first()
    )
    if not progress:
        return {"etapes": [], "completed": False, "xp_earned": 0,
                "carnet": {}, "metacognition": {}, "exercices_reussis": []}
    return _payload(progress)


@router.patch("/{parcours_id}/etape")
def save_etape(parcours_id: str, data: dict, db: Session = Depends(get_db)):
    user_id = data.get("user_id", 1)
    etape = data.get("etape")
    if etape not in ETAPES:
        raise HTTPException(status_code=400, detail="etape invalide")

    find_parcours(parcours_id)
    progress = get_or_create_progress(db, user_id, parcours_id)

    # Une étape validée le reste : on ne rétrograde jamais une progression.
    setattr(progress, ETAPES[etape], True)
    db.commit()
    db.refresh(progress)
    return {"status": "ok", "etape": etape, "etapes": _completed_etapes(progress)}


@router.patch("/{parcours_id}/carnet")
def save_carnet(parcours_id: str, data: dict, db: Session = Depends(get_db)):
    """Enregistre les réponses du carnet PISA (question de réflexion incluse)."""
    parcours = find_parcours(parcours_id)
    user_id = data.get("user_id", 1)
    reponses = data.get("reponses") or {}

    if not isinstance(reponses, dict) or not reponses:
        raise HTTPException(status_code=400, detail="Aucune réponse fournie")

    progress = get_or_create_progress(db, user_id, parcours_id)

    existing = {}
    if progress.carnet_json:
        try:
            existing = json.loads(progress.carnet_json)
        except (ValueError, TypeError):
            existing = {}
    existing.update({k: v for k, v in reponses.items() if not k.startswith("_")})
    progress.carnet_json = json.dumps(existing, ensure_ascii=False)

    attendues = [q.get("process") for q in parcours.get("carnet", [])]
    if all(existing.get(p) for p in attendues):
        progress.etape4_carnet = True

    db.commit()
    db.refresh(progress)
    return {"status": "ok", "etapes": _completed_etapes(progress)}


@router.post("/{parcours_id}/exercice")
def check_exercice(parcours_id: str, data: dict, db: Session = Depends(get_db)):
    """Corrige un exercice côté serveur et mémorise la réponse.

    La bonne réponse n'est jamais envoyée avec l'énoncé : elle n'est révélée
    qu'après trois tentatives, pour laisser la place à l'essai-erreur.
    """
    parcours = find_parcours(parcours_id)
    user_id = data.get("user_id", 1)
    exercise_id = data.get("exercise_id")
    response = data.get("response", "")

    exercise = next((e for e in parcours.get("exercises", []) if e["id"] == exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercice introuvable")

    correct = answer_matches(response, exercise.get("expected_answer", ""))

    record = (
        db.query(models.ExerciseResponse)
        .filter(
            models.ExerciseResponse.user_id == user_id,
            models.ExerciseResponse.exercise_id == exercise_id,
        )
        .first()
    )
    if record:
        record.attempts = (record.attempts or 0) + 1
        record.response = response
        record.is_correct = correct
    else:
        record = models.ExerciseResponse(
            user_id=user_id,
            exercise_id=exercise_id,
            response=response,
            is_correct=correct,
            attempts=1,
        )
        db.add(record)
    db.flush()

    progress = get_or_create_progress(db, user_id, parcours_id)
    reussis = []
    if progress.exercices_reussis:
        try:
            reussis = json.loads(progress.exercices_reussis)
        except (ValueError, TypeError):
            reussis = []

    if correct and exercise_id not in reussis:
        reussis.append(exercise_id)
    progress.exercices_reussis = json.dumps(reussis)

    total = len(parcours.get("exercises", []))
    if total and len(reussis) >= total:
        progress.etape5_exercices = True

    db.commit()

    payload = {
        "correct": correct,
        "attempts": record.attempts,
        "exercices_reussis": reussis,
        "etapes": _completed_etapes(progress),
    }
    if not correct and record.attempts >= 3:
        payload["expected_answer"] = exercise.get("expected_answer")
    return payload


@router.post("/{parcours_id}/complete")
def complete_parcours(parcours_id: str, data: dict, db: Session = Depends(get_db)):
    """Valide l'étape de métacognition et attribue les XP (une seule fois)."""
    parcours = find_parcours(parcours_id)
    user_id = data.get("user_id", 1)
    meta = data.get("metacognition") or {}

    progress = get_or_create_progress(db, user_id, parcours_id)

    if progress.completed:
        return {
            "status": "already_completed",
            "xp_earned": progress.xp_earned or 0,
            "total_xp": _user_xp(db, user_id),
        }

    carnet = {}
    if progress.carnet_json:
        try:
            carnet = json.loads(progress.carnet_json)
        except (ValueError, TypeError):
            carnet = {}
    carnet["_meta"] = meta
    progress.carnet_json = json.dumps(carnet, ensure_ascii=False)

    progress.etape6_metacognition = True
    progress.completed = True
    progress.xp_earned = parcours.get("xp_reward", 25)

    db.flush()
    total = _user_xp(db, user_id)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.xp = total

    db.commit()
    return {
        "status": "completed",
        "xp_earned": progress.xp_earned,
        "total_xp": total,
    }


def _user_xp(db: Session, user_id: int) -> int:
    rows = (
        db.query(models.ParcoursProgress.xp_earned)
        .filter(models.ParcoursProgress.user_id == user_id)
        .all()
    )
    return sum(r[0] or 0 for r in rows)
