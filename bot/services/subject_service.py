# bot/services/subject_service.py

import datetime
from sqlalchemy.orm import Session
from sqlalchemy import case
from bot.db.models import Subject, User, Absence, Grade
from typing import List
from datetime import datetime, time
from bot.db.models import CourseSubject

import logging

logger = logging.getLogger(__name__)



def create_subject(db: Session, user: User, name: str, professor: str, day: str, room: str, start_time: time, end_time: time, semestre: int, total_classes: int | None = None) -> Subject:
    """Cria uma nova matéria, agora com semestre."""
    db_subject = Subject(
        name=name, professor=professor, day_of_week=day, room=room,
        start_time=start_time, end_time=end_time, semestre=semestre,
        total_classes=total_classes, owner=user
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


# Frequência mínima exigida (comum na maioria das instituições brasileiras: 75%)
MINIMUM_ATTENDANCE_PERCENT = 75


def get_attendance_info(subject: Subject) -> dict | None:
    """
    Calcula a frequência de uma matéria a partir de total_classes e total_absences.
    Retorna None se o usuário ainda não informou o total de aulas previstas.
    """
    if not subject.total_classes or subject.total_classes <= 0:
        return None

    max_absences_allowed = int(subject.total_classes * (1 - MINIMUM_ATTENDANCE_PERCENT / 100))
    attended = max(subject.total_classes - subject.total_absences, 0)
    percent = (attended / subject.total_classes) * 100
    remaining_allowed = max_absences_allowed - subject.total_absences

    return {
        "percent": percent,
        "remaining_allowed": remaining_allowed,
        "at_risk": 0 <= remaining_allowed <= 2,
        "failed": remaining_allowed < 0,
    }

def get_subjects_by_user(db: Session, user: User) -> List[Subject]:
    """Retorna matérias de um usuário, ordenadas por dia e horário de início."""
    day_order_case = case(
        {"Segunda": 1, "Terça": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5, "Sábado": 6},
        value=Subject.day_of_week
    )
    # Ordena primeiro pelo dia, depois pelo horário de início
    return db.query(Subject).filter(Subject.user_id == user.user_id).order_by(day_order_case, Subject.start_time).all()

def get_subjects_by_day_of_week(db: Session, user: User, day_name: str) -> List[Subject]:
    """Retorna matérias de um dia, ordenadas por horário de início."""
    return db.query(Subject).filter(
        Subject.user_id == user.user_id,
        Subject.day_of_week == day_name
    ).order_by(Subject.start_time).all()

def check_conflict_with_existing(db: Session, user: User, day: str, start_time: time, end_time: time, exclude_subject_id: int | None = None) -> Subject | None:
    """
    Verifica se um horário (dia + início + fim) colide com alguma matéria que
    o usuário já tem cadastrada no mesmo dia. Retorna a matéria conflitante,
    ou None se não há conflito.
    `exclude_subject_id` ignora a própria matéria ao validar a edição do seu
    horário (senão ela sempre colidiria consigo mesma).
    """
    for subject in get_subjects_by_day_of_week(db, user, day):
        if exclude_subject_id is not None and subject.id == exclude_subject_id:
            continue
        if not subject.start_time or not subject.end_time:
            continue
        # Condição de sobreposição: (StartA < EndB) and (EndA > StartB)
        if start_time < subject.end_time and end_time > subject.start_time:
            return subject
    return None

def get_subject_by_id(db: Session, subject_id: int) -> Subject | None:
    return db.query(Subject).filter(Subject.id == subject_id).first()

def update_subject(db: Session, subject_id: int, new_data: dict) -> Subject | None:
    db_subject = get_subject_by_id(db, subject_id)
    if db_subject:
        for key, value in new_data.items():
            setattr(db_subject, key, value)
        db.commit()
        db.refresh(db_subject)
        return db_subject
    return None

def delete_subject_by_id(db: Session, subject_id: int) -> bool:
    subject_to_delete = get_subject_by_id(db, subject_id)
    if subject_to_delete:
        db.delete(subject_to_delete)
        db.commit()
        return True
    return False



def bulk_create_subjects(db: Session, user: User, subjects_data: list) -> dict:
    """
    Cria múltiplas matérias de uma vez a partir de uma lista de dicionários.
    Retorna um relatório com sucessos e falhas.
    """
    created_count = 0
    errors = []
    for index, data in enumerate(subjects_data, 1):
        try:
            # Converte os horários de string para time object
            start_time = datetime.strptime(data['horario_inicio'], '%H:%M').time()
            end_time = datetime.strptime(data['horario_fim'], '%H:%M').time()

            db_subject = Subject(
                name=data['nome'],
                professor=data.get('professor'), # .get() para campos opcionais
                day_of_week=data['dia_semana'],
                room=data.get('sala'),
                start_time=start_time,
                end_time=end_time,
                semestre=data.get('semestre'),
                owner=user
            )
            db.add(db_subject)
            created_count += 1
        except Exception as e:
            logger.error(f"Erro ao importar matéria na linha {index}: {e}")
            errors.append(f"Linha {index} ({data.get('nome', 'N/A')}): {e}")

    if errors:
        db.rollback() # Se houve qualquer erro, desfaz tudo para não salvar dados parciais
        return {"success": 0, "errors": errors}
    else:
        db.commit() # Se tudo deu certo, salva tudo de uma vez
        return {"success": created_count, "errors": []}
    
    
def bulk_create_from_course_subjects(db: Session, user: User, course_subjects: List[CourseSubject], semester_override: int | None = None) -> int:
    """Cria múltiplas matérias para um usuário a partir do catálogo mestre."""
    for course_sub in course_subjects:
        db_subject = Subject(
            name=course_sub.subject_name,
            professor=course_sub.professor_name,
            day_of_week=course_sub.day_of_week,
            room=course_sub.room,
            start_time=course_sub.start_time,
            end_time=course_sub.end_time,
            semestre=semester_override if semester_override is not None else course_sub.semester,
            owner=user
        )
        db.add(db_subject)
    
    db.commit()
    return len(course_subjects)