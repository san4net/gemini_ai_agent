import asyncio

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import utils

utils.configure_api_key()
retry_config = utils.retry_config()
model_llm = 'gemini-3.5-flash-lite'

APP_NAME = "default"  # Application
USER_ID = "santi"    # User

# Step 1: Create the LLM Agent
root_agent = Agent(
    model=Gemini(model=model_llm, retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",

)

# Step 2: Set up Session Management
session_service = InMemorySessionService()

# Step 3: Create the Runner
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

print("✅ Stateful agent initialized!")
print(f"   - Application: {APP_NAME}")
print(f"   - User: {USER_ID}")
print(f"   - Using: {session_service.__class__.__name__}")

async def run():
    # Fix 1: Pass required user_id keyword argument to create_session
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

    queries = [
        # "Hi, I am Sam! What is the capital of United States?",
        "Hello! What is my name?",
    ]

    for query in queries:
        print(f"\nUser: {query}")
        print("Agent: ", end="", flush=True)

        # Fix 2: role must be "user"
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session.id,
                new_message=message,
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts") and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text, end="", flush=True)
                elif isinstance(event.content, str):
                    print(event.content, end="", flush=True)
        print()

if __name__ == "__main__":
    asyncio.run(run())