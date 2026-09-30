import os
from groq import Groq

async def obter_resposta_ia(prompt: str) -> str:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("A chave GROQ_API_KEY não foi encontrada no arquivo .env")

    groq_client = Groq(api_key=api_key)
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Você é um assistente útil e amigável em um servidor do Discord."},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-20b",
    )
    return chat_completion.choices[0].message.content