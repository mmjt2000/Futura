"""
Suivi du bien-être : sommeil, mouvement, humeur, énergie.

Un enregistrement par jour et par utilisatrice. Les champs sont tous
facultatifs : l'écran ne force jamais une réponse.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/wellbeing", tags=["wellbeing"])


@router.get("/{user_id}")
def get_today(user_id: int, db: Session = Depends(get_db)):
    today = date.today()
    entry = (
        db.query(models.Wellbeing)
        .filter(models.Wellbeing.user_id == user_id, models.Wellbeing.date == today)
        .first()
    )
    if not entry:
        return {"date": today.isoformat(), "exists": False}
    return {
        "date": entry.date.isoformat(),
        "exists": True,
        "sleep_hours": entry.sleep_hours,
        "movement_minutes": entry.movement_minutes,
        "movement_type": entry.movement_type,
        "mood": entry.mood,
        "mood_note": entry.mood_note,
        "stress_level": entry.stress_level,
        "focus_level": entry.focus_level,
        "reflection_note": entry.reflection_note,
    }


@router.post("/{user_id}")
def save_today(user_id: int, data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisatrice introuvable")

    today = date.today()
    entry = (
        db.query(models.Wellbeing)
        .filter(models.Wellbeing.user_id == user_id, models.Wellbeing.date == today)
        .first()
    )
    if not entry:
        entry = models.Wellbeing(user_id=user_id, date=today)
        db.add(entry)

    allowed = (
        "sleep_hours", "sleep_quality", "movement_minutes", "movement_type",
        "mood", "mood_note", "stress_level", "focus_level",
        "breathing_sessions", "reflection_note", "boundary_note",
    )
    for field in allowed:
        if field in data:
            setattr(entry, field, data[field])

    db.commit()
    return {"status": "ok", "date": today.isoformat()}
