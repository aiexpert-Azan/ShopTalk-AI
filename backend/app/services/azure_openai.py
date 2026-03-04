from openai import AsyncAzureOpenAI
from app.core.config import settings

class AzureOpenAIService:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

    async def get_chat_response(self, messages: list, temperature: float = 0.7) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Azure OpenAI: {e}")
            raise e

ai_service = AzureOpenAIService()
