from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
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
        Your original LLM loader.
        This checks for Choreo and falls back to default OpenAI.
        """
        # This logic from your StoryGenerator was good, so we keep it.
        # It's flexible for different deployment environments.
        openai_api_key = os.getenv("CHOREO_OPENAI_CONNECTION_OPENAI_API_KEY")
        serviceurl = os.getenv("CHOREO_OPENAI_CONNECTION_SERVICEURL")

        if openai_api_key and serviceurl:
            return ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key, base_url=serviceurl, temperature=0.7)

        # Fallback to the key in the .env file
        return ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY, temperature=0.7)

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