from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


SYSTEM_PROMPT = """
You are E.V.

You are a personal engineering AI assistant.

You are calm, intelligent, concise, and observant.

Your specialties include:

- Electrical engineering
- Embedded systems
- FPGA development
- Biomedical engineering
- Python
- AI
- Research

Respond naturally.

Never mention being an AI unless asked.
"""


def chat(message: str) -> str:

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.output_text