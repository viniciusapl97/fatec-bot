from bot.services import user_service, access_token_service


def test_create_access_token_returns_plaintext_token(db, user):
    token = access_token_service.create_access_token(db, user)

    assert isinstance(token, str)
    assert len(token) > 20


def test_get_user_by_token_resolves_owner(db, user):
    token = access_token_service.create_access_token(db, user)

    resolved = access_token_service.get_user_by_token(db, token)

    assert resolved is not None
    assert resolved.user_id == user.user_id


def test_get_user_by_token_returns_none_for_invalid_token(db, user):
    access_token_service.create_access_token(db, user)

    assert access_token_service.get_user_by_token(db, "token-que-nao-existe") is None


def test_different_users_get_different_tokens(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")

    token_a = access_token_service.create_access_token(db, user)
    token_b = access_token_service.create_access_token(db, other_user)

    assert token_a != token_b
    assert access_token_service.get_user_by_token(db, token_a).user_id == user.user_id
    assert access_token_service.get_user_by_token(db, token_b).user_id == other_user.user_id


def test_revoke_all_access_tokens_invalidates_them(db, user):
    token_a = access_token_service.create_access_token(db, user)
    token_b = access_token_service.create_access_token(db, user)

    count = access_token_service.revoke_all_access_tokens(db, user)

    assert count == 2
    assert access_token_service.get_user_by_token(db, token_a) is None
    assert access_token_service.get_user_by_token(db, token_b) is None


def test_revoke_all_access_tokens_returns_zero_when_none_exist(db, user):
    assert access_token_service.revoke_all_access_tokens(db, user) == 0


def test_revoke_all_access_tokens_only_affects_owner(db, user):
    other_user, _ = user_service.get_or_create_user(db, 999, "Outro", "outro")
    token_mine = access_token_service.create_access_token(db, user)
    token_other = access_token_service.create_access_token(db, other_user)

    access_token_service.revoke_all_access_tokens(db, user)

    assert access_token_service.get_user_by_token(db, token_mine) is None
    assert access_token_service.get_user_by_token(db, token_other) is not None
