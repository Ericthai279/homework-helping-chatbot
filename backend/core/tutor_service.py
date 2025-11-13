from sqlalchemy.orm import Session
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from core.config import settings
from core import prompts
from models.user import User
from dotenv import load_dotenv
import os

load_dotenv()

class TutorService:

    @classmethod
    def _get_llm_multimodal(cls):
        """
        Load the multimodal (image + text) Ollama model for exercises.
        """
        return ChatOllama(
            base_url="http://localhost:11434",
            model="llava" # You must run 'ollama pull llava'
        )

    @classmethod
    def _get_llm_text_only(cls):
        """
        Load a faster, text-only Ollama model for other tasks.
        """
        return ChatOllama(
            base_url="http://localhost:11434",
            model="mistral-nemo" # You must run 'ollama pull mistral-nemo'
        )

    @classmethod
    async def get_initial_guidance(cls, prompt: str, base64_image: str | None = None) -> str:
        """
        Get the initial step-by-step guidance for an exercise.
        NOW ASYNCHRONOUS.
        """
        llm = cls._get_llm_multimodal() # Use 'llava' model
        
        message_content = []
        
        if base64_image:
            # If there's an image, use the image prompt
            message_content.append(SystemMessage(content=prompts.GUIDANCE_PROMPT_WITH_IMAGE))
            message_content.append(HumanMessage(
                content=[
                    {"type": "text", "text": prompt}, # Additional prompt (if any)
                    {
                        "type": "image_url",
                        "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" }
                    }
                ]
            ))
        else:
            # If text only
            message_content.append(SystemMessage(content=prompts.GUIDANCE_PROMPT.format(exercise_content=prompt)))

        chain = llm | StrOutputParser()
        # Use .ainvoke() for async
        return await chain.ainvoke(message_content)

    @classmethod
    async def check_user_answer(cls, exercise_content: str, user_answer: str) -> str:
        """
        Check if the user's answer is correct or incorrect.
        NOW ASYNCHRONOUS.
        """
        llm = cls._get_llm_text_only() # Use faster text model
        
        prompt = ChatPromptTemplate.from_template(prompts.CHECK_ANSWER_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        # Use .ainvoke() for async
        return await chain.ainvoke({
            "exercise_content": exercise_content,
            "user_answer": user_answer
        })

    @classmethod
    async def get_similar_exercise(cls, exercise_content: str) -> str:
        """
        Generate a similar exercise.
        NOW ASYNCHRONOUS.
        """
        llm = cls._get_llm_text_only() # Use faster text model
        
        prompt = ChatPromptTemplate.from_template(prompts.SIMILAR_EXERCISE_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        # Use .ainvoke() for async
        return await chain.ainvoke({"exercise_content": exercise_content})


class RoadmapService:
    @classmethod
    def _get_llm(cls):
        # Roadmap service only needs text, so we use the text model
        return TutorService._get_llm_text_only()

    @classmethod
    async def generate_roadmap(cls, user: User, learning_target: str) -> str:
        """
        Generate a roadmap (text only).
        NOW ASYNCHRONOUS.
        """
        llm = cls._get_llm()
        
        # We need a JSON parser for the roadmap, but using Str for now
        parser = StrOutputParser() 
        # (Ideally, we'd use JsonOutputParser + Pydantic Schema here)

        prompt = ChatPromptTemplate.from_template(prompts.ROADMAP_PROMPT)
        chain = prompt | llm | parser

        common_mistakes = ", ".join(user.profile_common_mistakes) if user.profile_common_mistakes else "N/A"

        # Use .ainvoke() for async
        return await chain.ainvoke({
            "profile_year": user.profile_year or "N/A",
            "profile_skill_level": user.profile_skill_level or "N/A",
            "profile_common_mistakes": common_mistakes,
            "learning_target": learning_target
        })