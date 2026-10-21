import asyncio

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.apps._configs import EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.adk.sessions import DatabaseSessionService  # Swapped to DatabaseSessionService
from google.genai import types
from google.genai.types import Content
from sqlalchemy import false

import utils

utils.configure_api_key()
retry_config = utils.retry_config()
model_llm = 'gemini-3.5-flash-lite'
APP_NAME = "compacting_app"  # Application
USER_ID = "santi"  # User

# Configured to use async PostgreSQL URL
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db"

# Global references initialized by setup function
session_service = None
runner = None


async def run(action: str):
    create_agent()

    if action == "create":
        session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
        print(f'session_id: {session.id}')
        queries = [
            "Hi, I am Sam! What is the capital of United States?",
            "Hello! What is my name?",
        ]
        for query in queries:
            print(f"\nUser: {query}")
            print("Agent: ", end="", flush=True)
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )
            await operation(message, session)

    elif action == "createandrunwithcompacting":
        session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
        print(f'compaction demo session_id: {session.id}')
        queries = [
            "What is the latest news about AI in healthcare?",
            "Who are the main companies involved in that?",
            "Tell me more about the second development you found.",
            "Who are the main companies involved in that?",
        ]
        for query in queries:
            print(f"\nUser: {query}")
            print("Agent: ", end="", flush=True)
            message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )
            await operation(message, session)

    else:
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID,
                                                    session_id="55d0bbcf-7d15-4691-8d37-d592ff43df17")
        print('searching for compaction event')
        for event in session.events:
            if event.actions and event.actions.compaction:
                print("compaction event found")
                print(f"details {event}")


async def operation(message: Content, session: Session | None):
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


def create_agent():
    global runner, session_service, app
    # Step 1: Create the LLM Agent
    text_agent = Agent(
        model=Gemini(model=model_llm, retry_options=retry_config),
        name="text_chat_bot",
        description="A text chatbot",
    )

    # Step 2: Use DatabaseSessionService to map tables over PostgreSQL
    session_service = DatabaseSessionService(db_url=DB_URL)

    # Step 3: Define Event Compaction for session history
    compacting_config = EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1,
    )

    research_agent = Agent(
        model=Gemini(model=model_llm, retry_options=retry_config),
        name="research_agent",
        description="Main research agent delegating tasks",
        sub_agents=[text_agent]
    )

    app = App(
        name=APP_NAME,
        root_agent=research_agent,
        events_compaction_config=compacting_config,
    )

    runner = Runner(app=app, session_service=session_service)

    print("Stateful PostgreSQL agent initialized!")
    print(f"   - Application: {APP_NAME}")
    print(f"   - User: {USER_ID}")
    print(f"   - Database: {DB_URL}")


if __name__ == "__main__":
    asyncio.run(run('createandrunwithcompacting'))
