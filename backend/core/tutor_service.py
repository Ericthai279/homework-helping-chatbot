from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from core.config import settings
from core import prompts
from core import llm_schemas
from models.user import User
from dotenv import load_dotenv
import os

load_dotenv()

class TutorService:

    @classmethod
    def _get_llm(cls):
        """
        This is the new LLM loader for Google Gemini.
        """
        return ChatGoogleGenerativeAI(
            model="gemini-pro-latest", 
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True,
            
            # --- THIS IS THE FIX ---
            # We are disabling the retries to stop spamming
            # the API when we hit a rate limit.
            max_retries=1 
            # ---------------------
        )

    @classmethod
    def get_initial_guidance(cls, exercise_content: str) -> str:
        """
        Gets the first "hint" for an exercise.
        """
        llm = cls._get_llm()
        prompt = ChatPromptTemplate.from_template(prompts.GUIDANCE_PROMPT)
        
        # We just want a string back, not JSON
        chain = prompt | llm | StrOutputParser()
        
        return chain.invoke({"exercise_content": exercise_content})

    @classmethod
    def check_user_answer(cls, exercise_content: str, user_answer: str) -> llm_schemas.CheckAnswerLLM:
        """
        Checks the user's answer and returns a structured response.
        """
        llm = cls._get_llm()
        parser = JsonOutputParser(pydantic_object=llm_schemas.CheckAnswerLLM)
        
        prompt = ChatPromptTemplate.from_template(
            prompts.CHECK_ANSWER_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | llm | parser
        
        return chain.invoke({
            "exercise_content": exercise_content,
            "user_answer": user_answer
        })

    @classmethod
    def get_similar_exercise(cls, exercise_content: str) -> llm_schemas.SimilarExerciseLLM:
        """
        Generates a new, similar exercise.
        """
        llm = cls._get_llm()
        parser = JsonOutputParser(pydantic_object=llm_schemas.SimilarExerciseLLM)
        
        prompt = ChatPromptTemplate.from_template(
            prompts.SIMILAR_EXERCISE_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | llm | parser
        
        return chain.invoke({"exercise_content": exercise_content})

class RoadmapService:

    @classmethod
    def _get_llm(cls):
        # We can reuse the same LLM logic
        return TutorService._get_llm()

    @classmethod
    def generate_roadmap(cls, user: User, learning_target: str) -> llm_schemas.RoadmapLLM:
        """
        Generates a complete, personalized roadmap (the slow, premium task).
        """
        llm = cls._get_llm()
        parser = JsonOutputParser(pydantic_object=llm_schemas.RoadmapLLM)

        prompt = ChatPromptTemplate.from_template(
            prompts.ROADMAP_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | llm | parser

        # Combine user profile data into a readable format
        common_mistakes = ", ".join(user.profile_common_mistakes) if user.profile_common_mistakes else "N/A"

        return chain.invoke({
            "profile_year": user.profile_year or "N/A",
            "profile_skill_level": user.profile_skill_level or "N/A",
            "profile_common_mistakes": common_mistakes,
            "learning_target": learning_target
        })