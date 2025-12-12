import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.services.ai import ai_service
from app.services.parser import content_parser
from app.bot.keyboards import kb_contact, kb_vacancies, kb_cancel


router = Router()
logger = logging.getLogger(__name__)


class RecruitState(StatesGroup):
    waiting_contact = State()
    waiting_vacancy = State()
    waiting_resume = State()
    chatting = State()


TEST_TASK_LINK = "Link to Test Case"
SUCCESS_MESSAGE_INSTRUCTION = (
    f"If the candidate's stack is suitable for us (Python, FastAPI, Redis), then reply with something like: "
    f"'Great, your experience is a good fit for us!'"
    f"And be sure to provide a link to the test task: {TEST_TASK_LINK}. "
    f"Add that you have 72 hours to complete it, and the result should be sent via reply message or a link to the git repository."
)
REJECT_MESSAGE_INSTRUCTION = (
    "If the candidate's stack isn't a good fit (for example, they only write in Java, 1C, or PHP), "
    "politely decline. Tell them we're specifically looking for Python developers with experience in asynchronous programming, "
    "but we'll save their resume in our database."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(RecruitState.waiting_contact)
    await message.answer(
        "Hi! I'm an AI recruiter at Abc Tech. 👋\n"
        "So that we can continue and I can offer you positions, "
        "please share your contact information (click the button below).",
        reply_markup=kb_contact,
    )


@router.message(RecruitState.waiting_contact, F.text)
async def warning_contact(message: Message):
    await message.answer(
        "Please use the button below to share your contact. ⬇️", reply_markup=kb_contact
    )


@router.message(RecruitState.waiting_contact, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact
    await state.update_data(
        phone=contact.phone_number,
        first_name=contact.first_name,
        last_name=contact.last_name,
        user_id=message.from_user.id,
    )

    await state.set_state(RecruitState.waiting_vacancy)
    await message.answer(
        f"Thank you, {contact.first_name}! The data has been saved. \n"
        "We currently have an open position on the Backend team. Select it to learn more.",
        reply_markup=kb_vacancies,
    )


@router.message(RecruitState.waiting_vacancy, F.text == "🐍 Python Backend Developer")
async def vacancy_python(message: Message, state: FSMContext):
    await state.set_state(RecruitState.waiting_resume)
    await message.answer(
        "Great choice! We're looking for a Middle Developer for the following stacks: **FastAPI, Redis, PostgreSQL**.\n\n"
        "Send me your resume in one of the following ways:\n"
        "1. **As a PDF file**\n"
        "2. **As a link** to HH.ru or LinkedIn (format https://hh.ru/resume/...)\n\n"
        "I'll analyze it and tell you what to do next.",
        reply_markup=kb_cancel,
        parse_mode="Markdown",
    )


@router.message(RecruitState.waiting_vacancy, F.text == "🔙 To the Beginning")
async def back_to_start(message: Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)


@router.message(RecruitState.waiting_resume, F.document)
async def handle_resume_pdf(message: Message, bot: Bot, state: FSMContext):
    if message.document.mime_type != "application/pdf":
        await message.answer("Please send your resume in **PDF** format.")
        return

    wait_msg = await message.answer("I'm downloading and reading your resume... ⏳")

    # Parsing
    file = await bot.download(message.document)
    text = await content_parser.extract_text_from_pdf(file.read())

    if not text or len(text) < 50:
        await wait_msg.edit_text(
            "Unable to read text from PDF. It may be a scan (image). Please send a text PDF or a link."
        )
        return

    # Saving context
    await state.update_data(resume_text=text[:4000])

    # AI Analyze. Creating a special prompt for this step.
    analysis_prompt = (
        f"Analyze the candidate's resume.\n"
        f"{SUCCESS_MESSAGE_INSTRUCTION}\n"
        f"{REJECT_MESSAGE_INSTRUCTION}"
    )

    ai_response = await ai_service.generate_response(
        user_text="Here's my resume. It's ok?",
        context=text[:4000],
        custom_system_prompt=analysis_prompt,  # Important: override the system prompt or supplement it.
    )

    await wait_msg.delete()
    await message.answer(ai_response, reply_markup=ReplyKeyboardRemove())

    # Switch to "chat" mode so that the candidate can ask questions about the test
    await state.set_state(RecruitState.chatting)


@router.message(RecruitState.waiting_resume, F.text.regexp(r"https?://[^\s]+"))
async def handle_resume_link(message: Message, state: FSMContext):
    url = message.text.strip()
    wait_msg = await message.answer("I click the link and read the profile... 🧐")

    text = await content_parser.extract_text_from_url(url)

    if not text:
        await wait_msg.edit_text(
            "I couldn't open the link (the profile might be private). It's better to send me the PDF file."
        )
        return

    await state.update_data(resume_text=text[:4000])

    analysis_prompt = (
        f"Analyze the candidate's profile using the link.\n"
        f"{SUCCESS_MESSAGE_INSTRUCTION}\n"
        f"{REJECT_MESSAGE_INSTRUCTION}"
    )

    ai_response = await ai_service.generate_response(
        user_text=f"Here's a link to my resume: {url}. It's ok?",
        context=text[:4000],
        custom_system_prompt=analysis_prompt,
    )

    await wait_msg.delete()
    await message.answer(ai_response, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RecruitState.chatting)


@router.message()
async def handle_any_text(message: Message, state: FSMContext):
    """
    FREE COMMUNICATION (AI Chat)
    Triggered when the user types text, but not a link or commands
    """
    data = await state.get_data()
    resume_context = data.get("resume_text", "")
    current_state = await state.get_state()

    ai_answer = None

    custom_prompt = ""

    # If a candidate asks questions INSTEAD of sending a resume
    if current_state == RecruitState.waiting_resume:
        custom_prompt = (
            "The candidate is at the resume submission stage, but instead of a file or link, they asked a question."
            "Your task:\n"
            "1. Answer their question briefly.\n"
            "2. Gently remind them that we need the resume (PDF or link) to proceed."
        )
        ai_answer = await ai_service.generate_response(
            user_text=message.text,
            context=resume_context,
            custom_system_prompt=custom_prompt,
        )

    # If we are already in chat mode (resume received)
    elif current_state == RecruitState.chatting:
        ai_answer = await ai_service.generate_response(
            user_text=message.text, context=resume_context
        )

    # If the state is unknown (for example, the user has not pressed start)
    else:
        ai_answer = "Please use the buttons menu below."

    if ai_answer:
        await message.answer(ai_answer)
