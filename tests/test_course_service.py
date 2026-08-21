from datetime import time

from bot.services import course_service
from bot.db.models import CourseSubject


def _cs(name, day, start, end, semester=1, course="ADS", shift="Noite"):
    return CourseSubject(
        course=course, shift=shift, semester=semester, subject_name=name,
        professor_name="Prof. X", day_of_week=day,
        start_time=time.fromisoformat(start), end_time=time.fromisoformat(end),
        room="A1",
    )


def test_check_schedule_conflict_returns_none_when_no_overlap(db):
    subjects = [
        _cs("Cálculo I", "Segunda", "19:00", "20:40"),
        _cs("Redes", "Segunda", "20:40", "22:20"),
    ]
    assert course_service.check_schedule_conflict(subjects) is None


def test_check_schedule_conflict_ignores_different_days(db):
    subjects = [
        _cs("Cálculo I", "Segunda", "19:00", "22:00"),
        _cs("Redes", "Terça", "19:00", "22:00"),
    ]
    assert course_service.check_schedule_conflict(subjects) is None


def test_check_schedule_conflict_detects_overlap(db):
    subjects = [
        _cs("Cálculo I", "Segunda", "19:00", "21:00"),
        _cs("Redes", "Segunda", "20:00", "22:00"),
    ]
    error = course_service.check_schedule_conflict(subjects)
    assert error is not None
    assert "Redes" in error


def test_get_available_courses(db):
    db.add(_cs("Cálculo I", "Segunda", "19:00", "20:40", course="ADS"))
    db.add(_cs("Física I", "Terça", "19:00", "20:40", course="Automação"))
    db.commit()

    courses = course_service.get_available_courses(db)
    assert set(courses) == {"ADS", "Automação"}


def test_get_ideal_grade_subjects_filters_by_course_shift_semester(db):
    db.add(_cs("Cálculo I", "Segunda", "19:00", "20:40", semester=1))
    db.add(_cs("Cálculo II", "Terça", "19:00", "20:40", semester=2))
    db.commit()

    subjects = course_service.get_ideal_grade_subjects(db, "ADS", "Noite", 1)
    assert [s.subject_name for s in subjects] == ["Cálculo I"]


def test_get_all_subjects_for_course_returns_every_semester(db):
    db.add(_cs("Cálculo I", "Segunda", "19:00", "20:40", semester=1))
    db.add(_cs("Cálculo II", "Terça", "19:00", "20:40", semester=2))
    db.commit()

    subjects = course_service.get_all_subjects_for_course(db, "ADS", "Noite")
    assert {s.subject_name for s in subjects} == {"Cálculo I", "Cálculo II"}


def test_get_subjects_by_ids(db):
    s1 = _cs("Cálculo I", "Segunda", "19:00", "20:40")
    s2 = _cs("Redes", "Terça", "19:00", "20:40")
    db.add(s1)
    db.add(s2)
    db.commit()

    found = course_service.get_subjects_by_ids(db, [s1.id, s2.id])
    assert {s.subject_name for s in found} == {"Cálculo I", "Redes"}
