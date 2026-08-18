import httpx

from app.config import settings


async def ask_llm(context: str,question: str) -> str:

    prompt = f"""
You are a intelligent AI assistant.

Answer the question ONLY using the context provided below and understand the question even if they are in shortfoem understand and give appropriate results.

If the answer is not present in the context, reply exactly with:

"I couldn't find that information in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url=url,
            headers={"x-goog-api-key": settings.GEMINI_API_KEY},
            json=payload
        )

    response.raise_for_status()

    response_data = response.json()
    return response_data["candidates"][0]["content"]["parts"][0]["text"]
