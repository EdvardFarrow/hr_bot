import pytest
from unittest.mock import ANY, patch, AsyncMock
from aiogram.types import Contact, Document
from app.bot.handlers import back_to_start, handle_resume_link, handle_resume_pdf
from app.bot.handlers import cmd_start, handle_contact, handle_any_text, RecruitState

pytestmark = pytest.mark.asyncio


async def test_cmd_start(mock_message, mock_state):
    """
    /start command test
    """
    await cmd_start(mock_message, mock_state)

    mock_state.set_state.assert_called_with(RecruitState.waiting_contact)
    mock_message.answer.assert_called_once()
    args, _ = mock_message.answer.call_args
    assert "Hi! I'm an AI recruiter" in args[0]


async def test_handle_contact(mock_message, mock_state):
    """
    Contact receiving test
    """
    mock_message.contact = Contact(
        phone_number="+123456789", first_name="Ivan", user_id=12345
    )

    await handle_contact(mock_message, mock_state)

    mock_state.update_data.assert_called_with(
        phone="+123456789", first_name="Ivan", last_name=None, user_id=12345
    )

    mock_state.set_state.assert_called_with(RecruitState.waiting_vacancy)


@patch("app.bot.handlers.ai_service")
async def test_ai_chat(mock_ai_service, mock_message, mock_state):
    """
    AI Challenge Test (MOCK Gemini)
    """
    mock_ai_service.generate_response = AsyncMock(return_value="I am a robot")

    mock_state.get_state = AsyncMock(return_value=RecruitState.chatting)
    mock_state.get_data = AsyncMock(return_value={"resume_text": "Some skills"})

    mock_message.text = "Hello!"

    await handle_any_text(mock_message, mock_state)

    mock_ai_service.generate_response.assert_called_once()

    mock_message.answer.assert_called_with("I am a robot")


@patch("app.bot.handlers.ai_service")
@patch("app.bot.handlers.content_parser")
async def test_handle_resume_pdf(mock_parser, mock_ai, mock_message, mock_state):

    mock_message.document = Document(
        file_id="123", file_unique_id="abc", mime_type="application/pdf"
    )

    import io

    fake_file = io.BytesIO(b"fake pdf content")

    mock_bot = AsyncMock()
    mock_bot.download.return_value = fake_file

    long_text = (
        "I am a Senior Python Developer with experience in FastAPI, Redis, Docker. " * 5
    )
    mock_parser.extract_text_from_pdf = AsyncMock(return_value=long_text)

    mock_ai.generate_response = AsyncMock(return_value="Great match!")

    from app.bot.handlers import handle_resume_pdf

    await handle_resume_pdf(mock_message, mock_bot, mock_state)

    mock_bot.download.assert_called_once()

    mock_state.set_state.assert_called_with(RecruitState.chatting)

    mock_message.answer.assert_called_with("Great match!", reply_markup=ANY)


@patch("app.bot.handlers.ai_service")
@patch("app.bot.handlers.content_parser")
async def test_handle_resume_link(mock_parser, mock_ai, mock_message, mock_state):
    mock_message.text = "https://hh.ru/resume/12345"

    long_text = "Experienced Python Backend Developer... " * 10
    mock_parser.extract_text_from_url = AsyncMock(return_value=long_text)

    mock_ai.generate_response = AsyncMock(return_value="Link Analysis Result")

    await handle_resume_link(mock_message, mock_state)

    mock_parser.extract_text_from_url.assert_called_with("https://hh.ru/resume/12345")
    mock_message.answer.assert_called()
    mock_message.delete.assert_not_called()
    mock_state.set_state.assert_called_with(RecruitState.chatting)


@patch("app.bot.handlers.content_parser")
async def test_handle_resume_link_fail(mock_parser, mock_message, mock_state):
    mock_message.text = "https://broken-link.com"

    mock_parser.extract_text_from_url = AsyncMock(return_value="")

    mock_wait_msg = AsyncMock()
    mock_message.answer = AsyncMock(return_value=mock_wait_msg)

    await handle_resume_link(mock_message, mock_state)

    mock_wait_msg.edit_text.assert_called()
    args, _ = mock_wait_msg.edit_text.call_args
    assert "couldn't open the link" in args[0]


@patch("app.bot.handlers.ai_service")
@patch("app.bot.handlers.content_parser")
async def test_handle_resume_pdf_scan_error(
    mock_parser, mock_ai, mock_message, mock_state
):
    from aiogram.types import Document

    mock_message.document = Document(
        file_id="1", file_unique_id="u", mime_type="application/pdf"
    )

    import io

    mock_bot = AsyncMock()
    mock_bot.download.return_value = io.BytesIO(b"scan")

    mock_parser.extract_text_from_pdf = AsyncMock(return_value="Scan")

    mock_wait_msg = AsyncMock()
    mock_message.answer = AsyncMock(return_value=mock_wait_msg)

    await handle_resume_pdf(mock_message, mock_bot, mock_state)

    mock_wait_msg.edit_text.assert_called()
    args, _ = mock_wait_msg.edit_text.call_args
    assert "Unable to read text" in args[0]

    mock_state.set_state.assert_not_called()


async def test_back_to_start(mock_message, mock_state):
    await back_to_start(mock_message, mock_state)

    mock_state.clear.assert_called_once()
    mock_message.answer.assert_called()
    args, _ = mock_message.answer.call_args
    assert "Hi! I'm an AI recruiter" in args[0]


async def test_handle_wrong_mime_type(mock_message, mock_state):
    from aiogram.types import Document

    mock_message.document = Document(
        file_id="1", file_unique_id="u", mime_type="image/jpeg"
    )

    mock_bot = AsyncMock()

    await handle_resume_pdf(mock_message, mock_bot, mock_state)

    mock_message.answer.assert_called()
    args, _ = mock_message.answer.call_args
    assert "Please send your resume in **PDF**" in args[0]


@patch("app.bot.handlers.ai_service")
async def test_chat_while_waiting_resume(mock_ai, mock_message, mock_state):
    mock_state.get_state = AsyncMock(return_value=RecruitState.waiting_resume)
    mock_message.text = "Why do I need to send it?"

    mock_ai.generate_response = AsyncMock(return_value="Because I said so")

    await handle_any_text(mock_message, mock_state)

    mock_ai.generate_response.assert_called_once()
    kwargs = mock_ai.generate_response.call_args.kwargs

    assert "instead of a file or link" in kwargs["custom_system_prompt"]
