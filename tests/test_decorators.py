import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.decorators import admin_only

# tests/conftest.py define ADMIN_USER_IDS="111" antes de bot.core.settings ser importado
ADMIN_ID = 111
NON_ADMIN_ID = 222


def _make_update(user_id, with_message=True):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.first_name = "Fulano"
    if with_message:
        update.message.reply_text = AsyncMock()
        update.callback_query = None
    else:
        update.message = None
        update.callback_query.answer = AsyncMock()
    return update


def test_admin_only_calls_wrapped_function_for_admin():
    wrapped_was_called = False

    @admin_only
    async def handler(update, context):
        nonlocal wrapped_was_called
        wrapped_was_called = True
        return "ok"

    update = _make_update(ADMIN_ID)
    result = asyncio.run(handler(update, MagicMock()))

    assert wrapped_was_called is True
    assert result == "ok"


def test_admin_only_blocks_non_admin_with_message():
    wrapped_was_called = False

    @admin_only
    async def handler(update, context):
        nonlocal wrapped_was_called
        wrapped_was_called = True

    update = _make_update(NON_ADMIN_ID, with_message=True)
    asyncio.run(handler(update, MagicMock()))

    assert wrapped_was_called is False
    update.message.reply_text.assert_awaited_once()


def test_admin_only_blocks_non_admin_via_callback_query():
    wrapped_was_called = False

    @admin_only
    async def handler(update, context):
        nonlocal wrapped_was_called
        wrapped_was_called = True

    update = _make_update(NON_ADMIN_ID, with_message=False)
    asyncio.run(handler(update, MagicMock()))

    assert wrapped_was_called is False
    update.callback_query.answer.assert_awaited_once_with("Acesso negado.", show_alert=True)
