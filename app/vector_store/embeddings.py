from typing import List
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.core.config import get_settings

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(openai.error.RateLimitError)
)
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts using OpenAI's API."""
    # Ensure texts are not too long
    texts = [text[:8191] for text in texts]
    
    response = await openai.Embedding.acreate(
        input=texts,
        model="text-embedding-ada-002"
    )
    
    return [data.embedding for data in response.data]
