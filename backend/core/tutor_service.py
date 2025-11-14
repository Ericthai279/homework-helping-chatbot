from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI # CORRECT GEMINI IMPORT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

from core import prompts
from models.user import User
# FIX: Import the Pydantic models from the new, separate schema file
from schemas.llm_output import CheckAnswerLLM, SimilarExerciseLLM, RoadmapLLM 

load_dotenv()

class TutorService:

    @classmethod
    def _get_llm_multimodal(cls):
        """
        Load the multimodal (image + text) model using Gemini 2.5 Flash.
        """
        # FIX 1: Use the correct model and refer to GOOGLE_API_KEY
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    @classmethod
    def _get_llm_text_only(cls):
        """
        Load a faster, text-only model using Gemini 2.5 Flash-Lite.
        """
        # FIX 2: Switched this back to the faster, text-only Gemini model 
        # (Since you are transitioning to Gemini and the OpenAI key is not working)
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", 
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    @classmethod
    async def get_initial_guidance(cls, prompt: str, base64_image: str | None = None) -> str:
        # Use the multimodal method (which uses the Gemini key)
        llm = cls._get_llm_multimodal() 
        message_content = []
        
        if base64_image:
            # If there's an image, use the multimodal prompt
            message_content.append(SystemMessage(content=prompts.GUIDANCE_PROMPT_WITH_IMAGE))
            message_content.append(HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" }
                    }
                ]
            ))
        else:
            # If text only, use the faster text model
            llm = cls._get_llm_text_only() 
            message_content.append(SystemMessage(content=prompts.GUIDANCE_PROMPT.format(exercise_content=prompt)))

        chain = llm | StrOutputParser()
        return await chain.ainvoke(message_content)

    @classmethod
    async def check_user_answer(cls, exercise_content: str, user_answer: str) -> CheckAnswerLLM:
        llm = cls._get_llm_text_only()
        # Use PydanticOutputParser for structured JSON output
        parser = PydanticOutputParser(pydantic_object=CheckAnswerLLM)
        prompt = ChatPromptTemplate.from_template(prompts.CHECK_ANSWER_PROMPT)
        chain = prompt | llm | parser
        
        return await chain.ainvoke({
            "exercise_content": exercise_content,
            "user_answer": user_answer,
            "format_instructions": parser.get_format_instructions()
        })

    @classmethod
    async def get_similar_exercise(cls, exercise_content: str) -> SimilarExerciseLLM:
        llm = cls._get_llm_text_only()
        parser = PydanticOutputParser(pydantic_object=SimilarExerciseLLM)
        prompt = ChatPromptTemplate.from_template(prompts.SIMILAR_EXERCISE_PROMPT)
        chain = prompt | llm | parser
        
        return await chain.ainvoke({
            "exercise_content": exercise_content,
            "format_instructions": parser.get_format_instructions()
        })


class RoadmapService:
    @classmethod
    def _get_llm(cls):
        return TutorService._get_llm_text_only()

    @classmethod
    async def generate_roadmap(cls, user: User, learning_target: str) -> RoadmapLLM:
        llm = cls._get_llm()
        parser = PydanticOutputParser(pydantic_object=RoadmapLLM)
        prompt = ChatPromptTemplate.from_template(prompts.ROADMAP_PROMPT)
        chain = prompt | llm | parser
        common_mistakes = ", ".join(user.profile_common_mistakes) if user.profile_common_mistakes else "N/A"
        return await chain.ainvoke({
            "profile_year": user.profile_year or "N/A",
            "profile_skill_level": user.profile_skill_level or "N/A",
            "profile_common_mistakes": common_mistakes,
            "learning_target": learning_target,
            "format_instructions": parser.get_format_instructions()
        })