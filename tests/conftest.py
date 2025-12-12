import pytest
from unittest.mock import AsyncMock
from aiogram.types import User, Chat, Message
from aiogram.fsm.context import FSMContext


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_message():
    message = AsyncMock(spec=Message)
    message.from_user = User(
        id=12345, is_bot=False, first_name="TestUser", last_name="Testov"
    )
    message.chat = Chat(id=12345, type="private")
    message.text = "Test message"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    state = AsyncMock(spec=FSMContext)
    storage = {}

    async def update_data(**kwargs):
        storage.update(kwargs)

    async def get_data():
        return storage

    state.update_data = AsyncMock(side_effect=update_data)
    state.get_data = AsyncMock(side_effect=get_data)
    return state
