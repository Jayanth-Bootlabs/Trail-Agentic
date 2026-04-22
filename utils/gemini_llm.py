from litellm import completion
from crewai.llms.base_llm import BaseLLM
import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("MODEL_NAME")

class GeminiLLM(BaseLLM):
    def __init__(self):
        super().__init__(model=model_name)

    def call(self, messages=None, **kwargs):
        try:
            response = completion(
                model=f"gemini/{model_name}",
                api_key=api_key,
                messages=messages
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

    def invoke(self, prompt: str):
        try:
            response = completion(
                model=f"gemini/{model_name}",
                api_key=api_key,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

    def __call__(self, prompt: str):
        return self.invoke(prompt)