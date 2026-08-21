from datetime import date, time
from decimal import Decimal

from bot.services import subject_service, activity_service, absence_service, grade_service
from bot.db.models import CourseSubject


def _make_subject(db, user, name="Cálculo I", day="Segunda", start="19:00", end="20:40", **kwargs):
    return subject_service.create_subject(
        db, user, name, "Prof. X", day, "A1",
        time.fromisoformat(start), time.fromisoformat(end), 1, **kwargs
    )


def test_create_subject_defaults_total_classes_to_none(db, user):
    subject = _make_subject(db, user)
    assert subject.total_classes is None
    assert subject.total_absences == 0


def test_create_subject_accepts_total_classes(db, user):
    subject = _make_subject(db, user, total_classes=40)
    assert subject.total_classes == 40


def test_get_subjects_by_user_orders_by_day_then_start_time(db, user):
    _make_subject(db, user, name="Quarta 10h", day="Quarta", start="10:00", end="11:40")
    _make_subject(db, user, name="Segunda 08h", day="Segunda", start="08:00", end="09:40")
    _make_subject(db, user, name="Segunda 07h", day="Segunda", start="07:00", end="08:40")

    ordered_names = [s.name for s in subject_service.get_subjects_by_user(db, user)]
    assert ordered_names == ["Segunda 07h", "Segunda 08h", "Quarta 10h"]


def test_get_subjects_by_user_only_returns_own_subjects(db, user):
    from bot.services import user_service
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    _make_subject(db, user, name="Minha matéria")
    _make_subject(db, other_user, name="Matéria de outra pessoa")

    names = [s.name for s in subject_service.get_subjects_by_user(db, user)]
    assert names == ["Minha matéria"]


def test_get_subjects_by_day_of_week_filters_correctly(db, user):
    _make_subject(db, user, name="Segunda", day="Segunda")
    _make_subject(db, user, name="Terça", day="Terça")

    names = [s.name for s in subject_service.get_subjects_by_day_of_week(db, user, "Terça")]
    assert names == ["Terça"]


def test_get_subject_by_id_returns_none_when_missing(db):
    assert subject_service.get_subject_by_id(db, 999) is None


def test_update_subject_changes_fields(db, user):
    subject = _make_subject(db, user)
    updated = subject_service.update_subject(db, subject.id, {"room": "B2", "semestre": 4})

    assert updated.room == "B2"
    assert updated.semestre == 4


def test_update_subject_returns_none_when_missing(db):
    assert subject_service.update_subject(db, 999, {"room": "B2"}) is None


def test_delete_subject_by_id_cascades_related_records(db, user):
    subject = _make_subject(db, user)
    activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")
    absence_service.add_absence(db, user, subject, date.today(), 1, None)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))

    deleted = subject_service.delete_subject_by_id(db, subject.id)

    assert deleted is True
    assert subject_service.get_subject_by_id(db, subject.id) is None
    assert activity_service.get_activities_by_subject(db, subject) == []


def test_delete_subject_by_id_returns_false_when_missing(db):
    assert subject_service.delete_subject_by_id(db, 999) is False


def test_bulk_create_subjects_success(db, user):
    data = [
        {"nome": "Cálculo I", "dia_semana": "Segunda", "horario_inicio": "19:00", "horario_fim": "20:40"},
        {"nome": "Redes", "dia_semana": "Terça", "horario_inicio": "19:00", "horario_fim": "22:40"},
    ]
    report = subject_service.bulk_create_subjects(db, user, data)

    assert report == {"success": 2, "errors": []}
    assert len(subject_service.get_subjects_by_user(db, user)) == 2


def test_bulk_create_subjects_rolls_back_everything_on_error(db, user):
    data = [
        {"nome": "Cálculo I", "dia_semana": "Segunda", "horario_inicio": "19:00", "horario_fim": "20:40"},
        {"nome": "Matéria Quebrada", "dia_semana": "Terça", "horario_inicio": "não é uma hora"},
    ]
    report = subject_service.bulk_create_subjects(db, user, data)

    assert report["success"] == 0
    assert len(report["errors"]) == 1
    assert subject_service.get_subjects_by_user(db, user) == []


def test_bulk_create_from_course_subjects_uses_catalog_semester_by_default(db, user):
    course_subjects = [
        CourseSubject(
            course="ADS", shift="Noite", semester=2, subject_name="Cálculo II",
            professor_name="Prof. Z", day_of_week="Quinta",
            start_time=time(19, 0), end_time=time(20, 40), room="C3",
        )
    ]
    count = subject_service.bulk_create_from_course_subjects(db, user, course_subjects)

    assert count == 1
    created = subject_service.get_subjects_by_user(db, user)[0]
    assert created.semestre == 2


def test_bulk_create_from_course_subjects_semester_override(db, user):
    course_subjects = [
        CourseSubject(
            course="ADS", shift="Noite", semester=2, subject_name="Cálculo II",
            professor_name="Prof. Z", day_of_week="Quinta",
            start_time=time(19, 0), end_time=time(20, 40), room="C3",
        )
    ]
    subject_service.bulk_create_from_course_subjects(db, user, course_subjects, semester_override=5)

    created = subject_service.get_subjects_by_user(db, user)[0]
    assert created.semestre == 5


def test_get_attendance_info_none_without_total_classes(db, user):
    subject = _make_subject(db, user)
    assert subject_service.get_attendance_info(subject) is None


def test_get_attendance_info_ok_status(db, user):
    subject = _make_subject(db, user, total_classes=40)
    absence_service.add_absence(db, user, subject, date.today(), 5, None)

    info = subject_service.get_attendance_info(subject)

    assert info["percent"] == 87.5
    assert info["remaining_allowed"] == 5
    assert info["at_risk"] is False
    assert info["failed"] is False


def test_get_attendance_info_at_risk_status(db, user):
    subject = _make_subject(db, user, total_classes=40)
    absence_service.add_absence(db, user, subject, date.today(), 9, None)

    info = subject_service.get_attendance_info(subject)

    assert info["remaining_allowed"] == 1
    assert info["at_risk"] is True
    assert info["failed"] is False


def test_get_attendance_info_failed_status(db, user):
    subject = _make_subject(db, user, total_classes=40)
    absence_service.add_absence(db, user, subject, date.today(), 12, None)

    info = subject_service.get_attendance_info(subject)

    assert info["remaining_allowed"] == -2
    assert info["at_risk"] is False
    assert info["failed"] is True


def test_check_conflict_with_existing_detects_overlap(db, user):
    _make_subject(db, user, day="Segunda", start="19:00", end="20:40")

    conflict = subject_service.check_conflict_with_existing(
        db, user, "Segunda", time(20, 0), time(21, 0)
    )
    assert conflict is not None
    assert conflict.name == "Cálculo I"


def test_check_conflict_with_existing_ignores_different_day(db, user):
    _make_subject(db, user, day="Segunda", start="19:00", end="20:40")

    conflict = subject_service.check_conflict_with_existing(
        db, user, "Terça", time(19, 0), time(20, 40)
    )
    assert conflict is None


def test_check_conflict_with_existing_allows_adjacent_times(db, user):
    _make_subject(db, user, day="Segunda", start="19:00", end="20:40")

    conflict = subject_service.check_conflict_with_existing(
        db, user, "Segunda", time(20, 40), time(22, 0)
    )
    assert conflict is None


def test_check_conflict_with_existing_returns_none_without_subjects(db, user):
    conflict = subject_service.check_conflict_with_existing(
        db, user, "Segunda", time(19, 0), time(20, 40)
    )
    assert conflict is None


def test_check_conflict_with_existing_excludes_own_subject(db, user):
    subject = _make_subject(db, user, day="Segunda", start="19:00", end="20:40")

    # Sem exclude_subject_id, a própria matéria "colidiria" consigo mesma.
    conflict = subject_service.check_conflict_with_existing(
        db, user, "Segunda", time(19, 0), time(20, 40), exclude_subject_id=subject.id
    )
    assert conflict is None


def test_check_conflict_with_existing_still_detects_others_when_excluding(db, user):
    subject = _make_subject(db, user, day="Segunda", start="19:00", end="20:40")
    _make_subject(db, user, name="Redes", day="Segunda", start="21:00", end="22:40")

    conflict = subject_service.check_conflict_with_existing(
        db, user, "Segunda", time(21, 30), time(23, 0), exclude_subject_id=subject.id
    )
    assert conflict is not None
    assert conflict.name == "Redes"
