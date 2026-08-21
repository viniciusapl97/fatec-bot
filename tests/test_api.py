from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient

from bot.services import access_token_service, subject_service, activity_service, absence_service, grade_service, user_service
from api.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_health_check_requires_no_auth():
    response = _client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_requires_authentication():
    response = _client().get("/me")
    assert response.status_code == 403  # sem header Authorization nenhum


def test_me_rejects_invalid_token():
    response = _client().get("/me", headers={"Authorization": "Bearer token-invalido"})
    assert response.status_code == 401


def test_me_returns_authenticated_user(db, user):
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user.user_id
    assert body["first_name"] == user.first_name


def test_list_subjects_returns_only_own_subjects(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    subject_service.create_subject(db, other_user, "Matéria de outra pessoa", "Prof. Z", "Segunda", "C1", None, None, 1)

    subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1, total_classes=40
    )
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/subjects", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Cálculo I"
    assert body[0]["total_classes"] == 40


def test_activities_requires_authentication():
    assert _client().get("/activities").status_code == 403


def test_list_activities_returns_only_own_and_embeds_subject_name(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    activity_service.create_activity(db, other_user, other_subject, "Não é meu", date.today(), None, "prova")

    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    activity_service.create_activity(db, user, subject, "P1", date(2026, 9, 10), "levar calculadora", "prova")
    activity_service.create_activity(db, user, subject, "Trabalho 1", date(2026, 9, 15), None, "trabalho")
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/activities", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all(item["subject_name"] == "Cálculo I" for item in body)


def test_list_activities_filters_by_type(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")
    activity_service.create_activity(db, user, subject, "T1", date.today(), None, "trabalho")
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/activities", params={"activity_type": "prova"}, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "P1"


def test_absences_requires_authentication():
    assert _client().get("/absences").status_code == 403


def test_list_absences_returns_only_own_and_embeds_subject_name(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    absence_service.add_absence(db, other_user, other_subject, date.today(), 1, None)

    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    absence_service.add_absence(db, user, subject, date.today(), 2, "atestado")
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/absences", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["subject_name"] == "Cálculo I"
    assert body[0]["quantity"] == 2
    assert body[0]["notes"] == "atestado"


def test_grades_requires_authentication():
    assert _client().get("/grades").status_code == 403


def test_list_grades_returns_only_own_and_embeds_subject_name(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    grade_service.add_grade(db, other_user, other_subject, "P1", Decimal("10.0"))

    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/grades", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["subject_name"] == "Cálculo I"
    assert body[0]["value"] == "7.50"


def test_subject_attendance_requires_authentication():
    assert _client().get("/subjects/1/attendance").status_code == 403


def test_subject_attendance_returns_404_for_other_users_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{other_subject.id}/attendance", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


def test_subject_attendance_returns_404_for_nonexistent_subject(db, user):
    token = access_token_service.create_access_token(db, user)

    response = _client().get("/subjects/99999/attendance", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


def test_subject_attendance_without_total_classes_returns_null_fields(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{subject.id}/attendance", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_classes"] is None
    assert body["percent"] is None
    assert body["remaining_allowed"] is None
    assert body["at_risk"] is False
    assert body["failed"] is False


def test_subject_attendance_computes_percent_and_risk(db, user):
    subject = subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1, total_classes=40
    )
    absence_service.add_absence(db, user, subject, date.today(), 9, None)
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{subject.id}/attendance", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_classes"] == 40
    assert body["total_absences"] == 9
    assert body["percent"] == 77.5
    assert body["remaining_allowed"] == 1
    assert body["at_risk"] is True
    assert body["failed"] is False


def test_subject_grades_requires_authentication():
    assert _client().get("/subjects/1/grades").status_code == 403


def test_subject_grades_returns_404_for_other_users_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{other_subject.id}/grades", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


def test_subject_grades_returns_grades_and_average(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    grade_service.add_grade(db, user, subject, "P2", Decimal("8.5"))
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{subject.id}/grades", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["subject_name"] == "Cálculo I"
    assert len(body["grades"]) == 2
    assert body["average"] == "8.00"


def test_subject_grades_average_is_null_when_no_grades(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().get(f"/subjects/{subject.id}/grades", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["grades"] == []
    assert body["average"] is None
