from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Date, Numeric, Time
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """
    Modelo que representa um usuário do Telegram no banco de dados.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True) 
    first_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    
    # Relações
    subjects = relationship("Subject", back_populates="owner", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="owner", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="owner", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="owner", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    professor = Column(String, nullable=True)
    day_of_week = Column(String, nullable=False)
    room = Column(String, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    semestre = Column(Integer, nullable=True)  # GARANTA QUE ESTA LINHA ESTÁ AQUI
    total_absences = Column(Integer, default=0, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))

    owner = relationship("User", back_populates="subjects")
    activities = relationship("Activity", back_populates="subject", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="subject", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="subject", cascade="all, delete-orphan")
    
    
    
class Activity(Base):
    """
    Modelo que representa uma atividade ou prova da agenda.
    """
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    notes = Column(String, nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    # Relações
    owner = relationship("User", back_populates="activities")
    subject = relationship("Subject", back_populates="activities")

class Absence(Base):
    __tablename__ = "absences"
    id = Column(Integer, primary_key=True, index=True)
    absence_date = Column(Date, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    notes = Column(String, nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    owner = relationship("User", back_populates="absences")
    subject = relationship("Subject", back_populates="absences")

class Grade(Base):
    """
    Modelo que representa uma nota (P1, P2, Trabalho, etc.).
    """
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # Ex: "P1", "Trabalho 1"
    value = Column(Numeric(4, 2), nullable=False) # Ex: 8.50, 10.00

    # Chaves estrangeiras
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    # Relações
    owner = relationship("User", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")