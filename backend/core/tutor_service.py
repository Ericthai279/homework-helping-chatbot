from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

from core import prompts
from models.user import User
# Import the Pydantic models we'll be using for parsing
from core.prompts import CheckAnswerLLM, SimilarExerciseLLM, RoadmapLLM

load_dotenv()

class TutorService:

    @classmethod
    def _get_llm_multimodal(cls):
        """
        Load the multimodal (image + text) model.
        We use GPT-4o for this.
        """
        return ChatOpenAI(
            model="gpt-4o",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    @classmethod
    def _get_llm_text_only(cls):
        """
        Load a faster, text-only model.
        We use GPT-3.5 Turbo for this.
        """
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    @classmethod
    async def get_initial_guidance(cls, prompt: str, base64_image: str | None = None) -> str:
        """
        Get the initial step-by-step guidance for an exercise.
        """
        llm = cls._get_llm_multimodal() # Use GPT-4o
        
        message_content = []
        
        if base64_image:
            # OpenAI's format for image messages
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
            # If no image, we can use the cheaper text-only model
            llm = cls._get_llm_text_only() 
            message_content.append(SystemMessage(content=prompts.GUIDANCE_PROMPT.format(exercise_content=prompt)))

        chain = llm | StrOutputParser()
        return await chain.ainvoke(message_content)

    @classmethod
    async def check_user_answer(cls, exercise_content: str, user_answer: str) -> CheckAnswerLLM:
        """
        Check if the user's answer is correct or incorrect.
        Returns a structured Pydantic object.
        """
        llm = cls._get_llm_text_only()
        
        parser = PydanticOutputParser(pydantic_object=CheckAnswerLLM)
        prompt = ChatPromptTemplate.from_template(prompts.CHECK_ANSWER_PROMPT)
        chain = prompt | llm | parser
        
        # This call now correctly passes all 3 required variables
        return await chain.ainvoke({
            "exercise_content": exercise_content,
            "user_answer": user_answer,
            "format_instructions": parser.get_format_instructions()
        })

    @classmethod
    async def get_similar_exercise(cls, exercise_content: str) -> SimilarExerciseLLM:
        """
        Generate a similar exercise.
        Returns a structured Pydantic object.
        """
        llm = cls._get_llm_text_only()
        
        parser = PydanticOutputParser(pydantic_object=SimilarExerciseLLM)
        prompt = ChatPromptTemplate.from_template(prompts.SIMILAR_EXERCISE_PROMPT)
        chain = prompt | llm | parser
        
        # This call now correctly passes the format_instructions
        return await chain.ainvoke({
            "exercise_content": exercise_content,
            "format_instructions": parser.get_format_instructions()
        })


class RoadmapService:
    @classmethod
    def _get_llm(cls):
        # Roadmap service only needs text
        return TutorService._get_llm_text_only()

    @classmethod
    async def generate_roadmap(cls, user: User, learning_target: str) -> RoadmapLLM:
        """
        Generate a roadmap (returns a Pydantic object).
        """
        llm = cls._get_llm()
        
        parser = PydanticOutputParser(pydantic_object=RoadmapLLM)
        prompt = ChatPromptTemplate.from_template(prompts.ROADMAP_PROMPT)
        chain = prompt | llm | parser

        common_mistakes = ", ".join(user.profile_common_mistakes) if user.profile_common_mistakes else "N/A"

        # This call now correctly passes all required variables
        return await chain.ainvoke({
            "profile_year": user.profile_year or "N/A",
            "profile_skill_level": user.profile_skill_level or "N/A",
            "profile_common_mistakes": common_mistakes,
            "learning_target": learning_target,
            "format_instructions": parser.get_format_instructions()
        })