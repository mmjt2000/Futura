"""
Profil des utilisatrices : identité, XP, badges, tableau de bord.

Les règles de gamification sont calculées à la volée à partir de
data/parcours.json et de parcours_progress : aucune donnée dénormalisée à
maintenir.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.routers.parcours import ETAPES, load_parcours_data

router = APIRouter(prefix="/api/users", tags=["users"])

# Les badges se mesurent en pourcentage de l'XP totale disponible, sinon les
# seuils absolus seraient atteints dès les trois premiers parcours.
BADGES = [
    {"id": "exploradora", "name": "Exploradora", "icon": "🌱", "ratio": 0.0,
     "description": "Has empezado tu viaje"},
    {"id": "aprendiz", "name": "Aprendiz", "icon": "📗", "ratio": 0.15,
     "description": "15 % del programa"},
    {"id": "creadora", "name": "Creadora", "icon": "🎨", "ratio": 0.35,
     "description": "35 % del programa"},
    {"id": "innovadora", "name": "Innovadora", "icon": "💡", "ratio": 0.60,
     "description": "60 % del programa"},
    {"id": "future_leader", "name": "Future Leader", "icon": "👑", "ratio": 0.85,
     "description": "85 % del programa"},
]


def _xp_total(db: Session, user_id: int) -> int:
    rows = (
        db.query(models.ParcoursProgress.xp_earned)
        .filter(models.ParcoursProgress.user_id == user_id)
        .all()
    )
    return sum(r[0] or 0 for r in rows)


def _progress_rows(db: Session, user_id: int):
    return {
        p.parcours_id: p
        for p in db.query(models.ParcoursProgress)
        .filter(models.ParcoursProgress.user_id == user_id)
        .all()
    }


def _badge_state(xp: int, max_xp: int):
    earned = []
    for badge in BADGES:
        threshold = round(max_xp * badge["ratio"])
        if xp >= threshold:
            earned.append({**badge, "threshold": threshold})
    return earned


def _summary(db: Session, user: models.User) -> dict:
    all_parcours = [
        p for p in load_parcours_data().get("parcours", [])
        if p["target_user"].lower() == user.name.lower()
    ]
    max_xp = sum(p["xp_reward"] for p in all_parcours) or 1
    xp = _xp_total(db, user.id)
    rows = _progress_rows(db, user.id)

    done = [p for p in all_parcours if p["id"] in rows and rows[p["id"]].completed]
    started = [p for p in all_parcours if p["id"] in rows and not rows[p["id"]].completed]

    earned = _badge_state(xp, max_xp)
    next_badge = None
    for badge in BADGES:
        threshold = round(max_xp * badge["ratio"])
        if xp < threshold:
            next_badge = {**badge, "threshold": threshold}
            break

    return {
        "id": user.id,
        "name": user.name,
        "country": user.country,
        "grade_level": user.grade_level,
        "xp": xp,
        "xp_max": max_xp,
        "xp_percent": round(100 * xp / max_xp),
        "parcours_total": len(all_parcours),
        "parcours_done": len(done),
        "parcours_started": len(started),
        "progress_percent": round(100 * len(done) / len(all_parcours)) if all_parcours else 0,
        "badges": earned,
        "next_badge": next_badge,
    }


@router.get("/")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.id).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "country": u.country,
            "grade_level": u.grade_level,
            "xp": _xp_total(db, u.id),
        }
        for u in users
    ]


@router.get("/{user_id}/summary")
def get_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisatrice introuvable")
    return _summary(db, user)


@router.get("/{user_id}/progress")
def get_all_progress(user_id: int, db: Session = Depends(get_db)):
    """Carte {parcours_id: progression} pour afficher l'état sur l'accueil."""
    rows = _progress_rows(db, user_id)
    result = {}
    for parcours_id, p in rows.items():
        etapes = [n for n, field in ETAPES.items() if getattr(p, field)]
        result[parcours_id] = {
            "etapes": etapes,
            "completed": bool(p.completed),
            "xp_earned": p.xp_earned or 0,
        }
    return result


@router.get("/{user_id}/sisters")
def get_sister(user_id: int, db: Session = Depends(get_db)):
    """Statistiques de l'autre sœur + son dernier parcours terminé."""
    me = db.query(models.User).filter(models.User.id == user_id).first()
    if not me:
        raise HTTPException(status_code=404, detail="Utilisatrice introuvable")

    sister = (
        db.query(models.User)
        .filter(models.User.id != user_id)
        .order_by(models.User.id)
        .first()
    )
    if not sister:
        raise HTTPException(status_code=404, detail="Aucune autre utilisatrice")

    summary = _summary(db, sister)

    last = (
        db.query(models.ParcoursProgress)
        .filter(
            models.ParcoursProgress.user_id == sister.id,
            models.ParcoursProgress.completed.is_(True),
        )
        .order_by(models.ParcoursProgress.updated_at.desc())
        .first()
    )
    last_parcours = None
    if last:
        for p in load_parcours_data().get("parcours", []):
            if p["id"] == last.parcours_id:
                last_parcours = {
                    "id": p["id"],
                    "title": p["title"],
                    "field": p["field"],
                    "xp_reward": p["xp_reward"],
                    "completed_at": last.updated_at.isoformat() if last.updated_at else None,
                }
                break

    return {
        "me": {"id": me.id, "name": me.name, "xp": _xp_total(db, me.id)},
        "sister": summary,
        "last_parcours": last_parcours,
    }
