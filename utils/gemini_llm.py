from litellm import completion
from crewai.llms.base_llm import BaseLLM
import os
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro")

class GeminiLLM(BaseLLM):
    def __init__(self):
        super().__init__(model=model_name)

    def call(self, messages=None, **kwargs):
        try:
            response = completion(
                model=f"vertex_ai/{model_name}",
                messages=messages,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

    def invoke(self, prompt: str):
        return self.call(
            messages=[{"role": "user", "content": prompt}]
        )

    async def generate(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.invoke(prompt)
        )

    def __call__(self, prompt: str):
        return self.invoke(prompt)

llm = GeminiLLM()