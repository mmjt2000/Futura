from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base

# ============================================
# 1. TABLE UTILISATEURS
# ============================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    country = Column(String(50), nullable=True)
    grade_level = Column(String(20), nullable=True)
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

# ============================================
# 2. TABLE MISSIONS (Ancien système)
# ============================================
class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_user = Column(String(50), nullable=False)
    xp_reward = Column(Integer, default=15)

# ============================================
# 3. TABLE PROGRESS (Ancien système)
# ============================================
class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mission_id = Column(Integer, ForeignKey("missions.id"))
    completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint('user_id', 'mission_id', name='uq_user_mission'),)

# ============================================
# 4. TABLE BADGES (Ancien système)
# ============================================
class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    earned_at = Column(DateTime, server_default=func.now())

# ============================================
# 5. TABLE PROJECTS (Ancien système)
# ============================================
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# ============================================
# 6. TABLE PARCOURS (Métadonnées)
# ============================================
class Parcours(Base):
    __tablename__ = "parcours"
    id = Column(String(100), primary_key=True)
    target_user = Column(String(50), nullable=False)
    field = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    xp_reward = Column(Integer, default=25)
    prerequisite = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# ============================================
# 7. TABLE PARCOURS_PROGRESS (NOUVELLE - progression des parcours)
# ============================================
class ParcoursProgress(Base):
    __tablename__ = "parcours_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parcours_id = Column(String(100), nullable=False)
    etape1_contexte = Column(Boolean, default=False)
    etape2_khan = Column(Boolean, default=False)
    etape3_labo = Column(Boolean, default=False)
    etape4_carnet = Column(Boolean, default=False)
    etape5_exercices = Column(Boolean, default=False)
    etape6_metacognition = Column(Boolean, default=False)
    carnet_json = Column(Text, nullable=True)
    exercices_reussis = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    xp_earned = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint('user_id', 'parcours_id', name='uq_user_parcours'),)

# ============================================
# 8. TABLE EXERCISE_RESPONSES
# ============================================
class ExerciseResponse(Base):
    __tablename__ = "exercise_responses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(String(100), nullable=False)
    response = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

# ============================================
# 9. TABLE WELLBEING
# ============================================
class Wellbeing(Base):
    __tablename__ = "wellbeing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    movement_minutes = Column(Integer, nullable=True)
    movement_type = Column(String(50), nullable=True)
    mood = Column(String(10), nullable=True)
    mood_note = Column(Text, nullable=True)
    stress_level = Column(Integer, nullable=True)
    focus_level = Column(Integer, nullable=True)
    breathing_sessions = Column(Integer, default=0)
    reflection_note = Column(Text, nullable=True)
    boundary_note = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_user_date'),)