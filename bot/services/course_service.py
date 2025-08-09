
from sqlalchemy.orm import Session
from typing import List
from bot.db.models import CourseSubject

def get_available_courses(db: Session) -> List[str]:
    """Retorna uma lista de nomes de cursos únicos."""
    return [row[0] for row in db.query(CourseSubject.course).distinct().all()]

def get_ideal_grade_subjects(db: Session, course: str, shift: str, semester: int) -> List[CourseSubject]:
    """Busca todas as matérias da grade ideal para um curso, turno e semestre."""
    return db.query(CourseSubject).filter_by(
        course=course, shift=shift, semester=semester
    ).order_by(CourseSubject.day_of_week, CourseSubject.start_time).all()

def get_all_subjects_for_course(db: Session, course: str, shift: str) -> List[CourseSubject]:
    """Busca TODAS as matérias de um curso e turno para a montagem da grade personalizada."""
    return db.query(CourseSubject).filter_by(
        course=course, shift=shift
    ).order_by(CourseSubject.semester, CourseSubject.day_of_week, CourseSubject.start_time).all()

def get_subjects_by_ids(db: Session, ids: List[int]) -> List[CourseSubject]:
    """Busca uma lista de matérias do catálogo a partir de seus IDs."""
    return db.query(CourseSubject).filter(CourseSubject.id.in_(ids)).all()

def check_schedule_conflict(subjects: List[CourseSubject]) -> str | None:
    """
    Verifica se há conflito de horário em uma lista de matérias.
    Retorna uma string de erro se houver conflito, senão retorna None.
    """
    schedule = {} # Ex: {"Segunda": [(19:00, 20:40), ...]}
    for subject in subjects:
        day = subject.day_of_week
        if day not in schedule:
            schedule[day] = []
        
        # Verifica se o novo horário colide com algum já adicionado
        for start, end in schedule[day]:
            # Condição de sobreposição: (StartA < EndB) and (EndA > StartB)
            if subject.start_time < end and subject.end_time > start:
                return (
                    f"Conflito de horário detectado!\n"
                    f"A matéria '{subject.subject_name}' ({subject.start_time.strftime('%H:%M')}-{subject.end_time.strftime('%H:%M')}) "
                    f"colide com outra matéria já selecionada no mesmo dia."
                )
        schedule[day].append((subject.start_time, subject.end_time))
    return None