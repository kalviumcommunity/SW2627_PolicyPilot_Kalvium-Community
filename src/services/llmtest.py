import os
import logging

from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError


load_dotenv()

BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("CHAT_MODEL")


# --------------------------------------------------
# 2. Validate environment configuration
# --------------------------------------------------

if not BASE_URL:
    raise ValueError("API_BASE_URL is missing from .env")

if not API_KEY:
    raise ValueError("API_KEY is missing from .env")

if not MODEL:
    raise ValueError("CHAT_MODEL is missing from .env")


# --------------------------------------------------
# 3. Configure logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------------------------
# 4. Create OpenAI-compatible client
# --------------------------------------------------

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)


# --------------------------------------------------
# 5. Create system and user messages
# --------------------------------------------------

messages = [
    {
        "role": "system",
        "content": (
            "You are a concise and helpful assistant. "
            "Answer clearly and accurately."
        )
    },
    {
        "role": "user",
        "content": "What is RAG? Explain it in one simple sentence."
    }
]


# --------------------------------------------------
# 6. Send chat completion request
# --------------------------------------------------

try:

    # Log outgoing request
    logging.info("REQUEST MODEL: %s", MODEL)
    logging.info("REQUEST MESSAGES: %s", messages)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    # --------------------------------------------------
    # 7. Read the model's response
    # --------------------------------------------------

    answer = response.choices[0].message.content

    print("\n========== MODEL RESPONSE ==========")
    print(answer)
    print("====================================\n")

    # --------------------------------------------------
    # 8. Log response
    # --------------------------------------------------

    logging.info("RESPONSE: %s", answer)

    # --------------------------------------------------
    # 9. Log token usage if available
    # --------------------------------------------------

    if response.usage:
        logging.info("TOKEN USAGE: %s", response.usage)
    else:
        logging.info("TOKEN USAGE: Not provided by the API")


except AuthenticationError:
    print(
        "Authentication failed (401): "
        "Please check your API_KEY in the .env file."
    )


except RateLimitError:
    print(
        "Rate limit/quota error (429): "
        "Please check your API quota or wait and try again."
    )

except Exception as error:
    print(f"API request failed: {error}")