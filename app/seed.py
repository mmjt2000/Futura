"""
Initialisation des données de base de FUTURA.

Crée les deux profils (Maryse et Laeticia) au premier démarrage.
Le contenu pédagogique reste dans data/parcours.json : il n'est pas dupliqué
en base, ce qui permet de l'éditer sans migration.
"""
from app.database import SessionLocal
from app import models

USERS = [
    {
        "id": 1,
        "name": "Maryse",
        "country": "México",
        "grade_level": "3° secundaria",
    },
    {
        "id": 2,
        "name": "Laeticia",
        "country": "República Dominicana",
        "grade_level": "4° secundaria",
    },
]


def seed_users() -> None:
    """Crée les profils manquants. Idempotent : ne touche à rien s'ils existent."""
    db = SessionLocal()
    try:
        for user in USERS:
            exists = db.query(models.User).filter(models.User.id == user["id"]).first()
            if exists:
                continue
            # Même identifiant libre mais autre nom (base réutilisée) : on ne
            # écrase pas, on cherche par nom avant d'insérer.
            by_name = db.query(models.User).filter(models.User.name == user["name"]).first()
            if by_name:
                continue
            db.add(models.User(**user))
        db.commit()
    finally:
        db.close()
