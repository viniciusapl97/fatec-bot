import hashlib
import hmac
import time as time_module
from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient

from bot.core.settings import TELEGRAM_TOKEN
from bot.services import access_token_service, subject_service, activity_service, absence_service, grade_service, user_service
from api.main import app


def _client() -> TestClient:
    return TestClient(app)


def _sign_telegram_payload(**overrides) -> dict:
    """Monta um payload do Telegram Login Widget assinado com TELEGRAM_TOKEN, do jeito que o Telegram faria de verdade."""
    payload = {
        "id": 12345,
        "first_name": "Ana",
        "username": "ana_tg",
        "auth_date": int(time_module.time()),
    }
    payload.update(overrides)

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode("utf-8")).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return payload


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


# --- POST/PATCH/DELETE /subjects ---------------------------------------------

def test_create_subject_requires_authentication():
    assert _client().post("/subjects", json={"name": "X", "day_of_week": "Segunda"}).status_code == 403


def test_create_subject_success(db, user):
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/subjects",
        json={
            "name": "Cálculo I", "professor": "Prof. X", "day_of_week": "Segunda", "room": "A1",
            "start_time": "19:00", "end_time": "20:40", "semestre": 1, "total_classes": 40,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cálculo I"
    assert body["total_classes"] == 40
    assert body["total_absences"] == 0


def test_create_subject_rejects_invalid_day_of_week(db, user):
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/subjects",
        json={"name": "Cálculo I", "day_of_week": "Domingo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_subject_rejects_time_conflict(db, user):
    subject_service.create_subject(
        db, user, "Cálculo I", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1
    )
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/subjects",
        json={"name": "Física I", "day_of_week": "Segunda", "start_time": "19:30", "end_time": "21:00"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_update_subject_returns_404_for_other_users_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/subjects/{other_subject.id}", json={"name": "Hackeado"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_update_subject_partial_update(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1, total_classes=40)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/subjects/{subject.id}", json={"room": "B2"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["room"] == "B2"
    assert body["name"] == "Cálculo I"
    assert body["total_classes"] == 40


def test_update_subject_clears_total_classes_with_explicit_null(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1, total_classes=40)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/subjects/{subject.id}", json={"total_classes": None}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["total_classes"] is None


def test_update_subject_rejects_time_conflict(db, user):
    subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", time(19, 0), time(20, 40), 1)
    other = subject_service.create_subject(db, user, "Física I", "Prof. Y", "Terça", "B1", time(19, 0), time(20, 40), 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/subjects/{other.id}", json={"day_of_week": "Segunda"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 409


def test_delete_subject_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().delete(f"/subjects/{subject.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert subject_service.get_subject_by_id(db, subject.id) is None


def test_delete_subject_returns_404_for_other_users_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().delete(f"/subjects/{other_subject.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


# --- POST/PATCH/DELETE /activities --------------------------------------------

def test_create_activity_requires_own_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/activities",
        json={"subject_id": other_subject.id, "activity_type": "prova", "name": "P1", "due_date": "2026-09-10"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_create_activity_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/activities",
        json={"subject_id": subject.id, "activity_type": "prova", "name": "P1", "due_date": "2026-09-10", "notes": "levar calculadora"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "P1"
    assert body["subject_name"] == "Cálculo I"
    assert body["notes"] == "levar calculadora"


def test_update_activity_returns_404_for_other_users_activity(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    other_activity = activity_service.create_activity(db, other_user, other_subject, "P1", date.today(), None, "prova")
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/activities/{other_activity.id}", json={"name": "Hackeado"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_update_activity_can_move_to_own_subject(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    other_subject = subject_service.create_subject(db, user, "Física I", "Prof. Y", "Terça", "B1", None, None, 1)
    activity = activity_service.create_activity(db, user, subject, "P1", date(2026, 9, 10), None, "prova")
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/activities/{activity.id}", json={"subject_id": other_subject.id}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["subject_name"] == "Física I"


def test_update_activity_rejects_move_to_other_users_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    activity = activity_service.create_activity(db, user, subject, "P1", date(2026, 9, 10), None, "prova")
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/activities/{activity.id}", json={"subject_id": other_subject.id}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_activity_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    activity = activity_service.create_activity(db, user, subject, "P1", date.today(), None, "prova")
    token = access_token_service.create_access_token(db, user)

    response = _client().delete(f"/activities/{activity.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert activity_service.get_activity_by_id(db, activity.id) is None


# --- POST/PATCH/DELETE /absences ------------------------------------------------

def test_create_absence_requires_own_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/absences",
        json={"subject_id": other_subject.id, "absence_date": "2026-08-20", "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_create_absence_updates_subject_total(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/absences",
        json={"subject_id": subject.id, "absence_date": "2026-08-20", "quantity": 2, "notes": "atestado"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["quantity"] == 2
    assert body["subject_name"] == "Cálculo I"
    db.refresh(subject)
    assert subject.total_absences == 2


def test_create_absence_rejects_non_positive_quantity(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/absences",
        json={"subject_id": subject.id, "absence_date": "2026-08-20", "quantity": 0},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_update_absence_adjusts_subject_total(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    absence = absence_service.add_absence(db, user, subject, date.today(), 2, None)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/absences/{absence.id}", json={"quantity": 5}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 5
    db.refresh(subject)
    assert subject.total_absences == 5


def test_update_absence_returns_404_for_other_users_absence(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    other_absence = absence_service.add_absence(db, other_user, other_subject, date.today(), 1, None)
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/absences/{other_absence.id}", json={"quantity": 3}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_absence_adjusts_subject_total(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    absence = absence_service.add_absence(db, user, subject, date.today(), 3, None)
    token = access_token_service.create_access_token(db, user)

    response = _client().delete(f"/absences/{absence.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    db.refresh(subject)
    assert subject.total_absences == 0


# --- POST/PATCH/DELETE /grades ---------------------------------------------------

def test_create_grade_requires_own_subject(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/grades",
        json={"subject_id": other_subject.id, "name": "P1", "value": "7.5"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_create_grade_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/grades",
        json={"subject_id": subject.id, "name": "P1", "value": "7.5"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["value"] == "7.50"
    assert body["subject_name"] == "Cálculo I"


def test_create_grade_rejects_negative_value(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    token = access_token_service.create_access_token(db, user)

    response = _client().post(
        "/grades",
        json={"subject_id": subject.id, "name": "P1", "value": "-1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_update_grade_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    grade = grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/grades/{grade.id}", json={"name": "P1 (revisão)", "value": "9.0"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "P1 (revisão)"
    assert body["value"] == "9.00"


def test_update_grade_returns_404_for_other_users_grade(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    other_subject = subject_service.create_subject(db, other_user, "Matéria de outro", "Prof. Z", "Segunda", "C1", None, None, 1)
    other_grade = grade_service.add_grade(db, other_user, other_subject, "P1", Decimal("10.0"))
    token = access_token_service.create_access_token(db, user)

    response = _client().patch(
        f"/grades/{other_grade.id}", json={"name": "Hackeado", "value": "0"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_grade_success(db, user):
    subject = subject_service.create_subject(db, user, "Cálculo I", "Prof. X", "Segunda", "A1", None, None, 1)
    grade = grade_service.add_grade(db, user, subject, "P1", Decimal("7.5"))
    token = access_token_service.create_access_token(db, user)

    response = _client().delete(f"/grades/{grade.id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert grade_service.get_grade_by_id(db, grade.id) is None


# --- POST /auth/telegram -------------------------------------------------------

def test_telegram_login_creates_user_and_returns_working_token(db):
    payload = _sign_telegram_payload(id=555, first_name="Beto", username="beto_tg")

    response = _client().post("/auth/telegram", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    token = body["access_token"]

    me_response = _client().get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["user_id"] == 555
    assert me_response.json()["first_name"] == "Beto"


def test_telegram_login_reuses_existing_user(db, user):
    payload = _sign_telegram_payload(id=user.user_id, first_name=user.first_name, username=user.username)

    response = _client().post("/auth/telegram", json=payload)

    assert response.status_code == 200
    token = response.json()["access_token"]
    me_response = _client().get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.json()["user_id"] == user.user_id


def test_telegram_login_rejects_tampered_payload():
    payload = _sign_telegram_payload(id=555, first_name="Beto")
    payload["first_name"] = "Invasor"  # muda o payload sem re-assinar

    response = _client().post("/auth/telegram", json=payload)

    assert response.status_code == 401


def test_telegram_login_rejects_wrong_hash():
    payload = _sign_telegram_payload(id=555, first_name="Beto")
    payload["hash"] = "0" * 64

    response = _client().post("/auth/telegram", json=payload)

    assert response.status_code == 401


def test_telegram_login_rejects_expired_auth_date():
    payload = _sign_telegram_payload(id=555, first_name="Beto", auth_date=int(time_module.time()) - 999999)

    response = _client().post("/auth/telegram", json=payload)

    assert response.status_code == 401
