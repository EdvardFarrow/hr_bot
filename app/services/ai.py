import google.generativeai as genai
from app.config import settings
import logging


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an AI recruiter for the IT company "Ave Tech". 
Your main goal is the primary screening of candidates.

**Tone and Style:**
- Friendly and informal.
- Professional but not bureaucratic.
- Concise and to the point.

**Tech Stack to look for:**
- Python, FastAPI, Redis, Docker, Aiogram, Pydantic.

**Instructions:**
1. **Salary/Benefits Questions:** If the user asks about salary, working hours, or vacation, politely deflect. Use a variation of this phrase: "These organizational details are discussed at the technical interview or offer stage. Right now, I need to understand your technical background. Do you have questions about the tasks?"
2. **Resume Analysis:** - If the user sends a resume (text provided in CONTEXT), analyze their tech stack.
    - If their stack matches ours (Python/FastAPI): Praise them (informally) and suggest sending the test assignment.
    - If the stack does NOT match (e.g., Java/C#): Politely refuse, saying we are looking for Python developers.
3. **General Chat:** Answer questions about the tech stack or the test assignment.
4. **Safety:** Do not invent facts about the company that are not provided here.
"""

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY.get_secret_value())
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def generate_response(self, user_text: str, context: str = "") -> str:
        """
        user_text: user message
        context: for example, the text of the resume, if it was sent earlier
        """
        prompt = f"{SYSTEM_PROMPT}\n\n"
        
        if context:
            prompt += f"CONTEXT (candidate's resume):\n{context}\n\n"
            
        prompt += f"CANDIDATE'S MESSAGE: {user_text}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"AI Error: {e}")
            return "My neurons are confused. Let's try again?"

ai_service = AIService()