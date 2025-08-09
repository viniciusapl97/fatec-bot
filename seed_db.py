# seed_db.py

import json
from datetime import datetime
from bot.db.base import SessionLocal, engine
from bot.db.models import CourseSubject, Base

def seed_database():
    """
    Lê o arquivo JSON e popula a tabela de matérias do curso usando uma
    estratégia de 'update ou insert' (upsert) para manter os dados existentes.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Lendo o arquivo courses.json...")
    try:
        with open('data/courses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERRO: Não foi possível ler o arquivo 'data/courses.json'. Erro: {e}")
        return

    print("Sincronizando o catálogo de matérias...")
    subjects_in_json = []
    for course in data.get('courses', []):
        for shift in course.get('shifts', []):
            for subject_data in shift.get('subjects', []):
                
                # Chave única para identificar uma matéria
                subject_key = (course['name'], shift['name'], subject_data['subject_name'])
                subjects_in_json.append(subject_key)

                # Procura se a matéria já existe no banco
                existing_subject = db.query(CourseSubject).filter_by(
                    course=course['name'],
                    shift=shift['name'],
                    subject_name=subject_data['subject_name']
                ).first()
                
                if existing_subject:
                    # Se existe, ATUALIZA
                    existing_subject.semester = subject_data['semester']
                    existing_subject.professor_name = subject_data.get('professor_name')
                    existing_subject.day_of_week = subject_data['day_of_week']
                    existing_subject.start_time = datetime.strptime(subject_data['start_time'], '%H:%M').time()
                    existing_subject.end_time = datetime.strptime(subject_data['end_time'], '%H:%M').time()
                    existing_subject.room = subject_data.get('room')
                else:
                    # Se não existe, CRIA
                    new_subject = CourseSubject(
                        course=course['name'],
                        shift=shift['name'],
                        semester=subject_data['semester'],
                        subject_name=subject_data['subject_name'],
                        professor_name=subject_data.get('professor_name'),
                        day_of_week=subject_data['day_of_week'],
                        start_time=datetime.strptime(subject_data['start_time'], '%H:%M').time(),
                        end_time=datetime.strptime(subject_data['end_time'], '%H:%M').time(),
                        room=subject_data.get('room')
                    )
                    db.add(new_subject)
    
    # Opcional: Remove matérias que estão no banco mas não estão mais no JSON
    print("Verificando matérias para remover...")
    all_db_subjects = db.query(CourseSubject).all()
    for db_sub in all_db_subjects:
        db_key = (db_sub.course, db_sub.shift, db_sub.subject_name)
        if db_key not in subjects_in_json:
            print(f"Removendo matéria obsoleta: {db_sub.subject_name}")
            db.delete(db_sub)
            
    db.commit()
    db.close()
    
    print("Sincronização do catálogo concluída com sucesso!")

if __name__ == "__main__":
    seed_database()