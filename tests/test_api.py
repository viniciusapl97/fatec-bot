from datetime import time

from fastapi.testclient import TestClient

from bot.services import access_token_service, subject_service
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
    from bot.services import user_service
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
