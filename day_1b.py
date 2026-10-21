import asyncio
import utils

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool


# import os
# from kaggle_secrets import UserSecretsClient

# os.environ.setdefault('GOOGLE_API_KEY', GOOGLE_API_KEY)
utils.configure_api_key()
retry_config = utils.retry_config()
model_llm ='gemini-3.5-flash-lite'

# Research Agent: Its job is to use the google_search tool and present findings.
research_agent = Agent(
    name="ResearchAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""You are a specialized research agent. Your only job is to use the
    google_search tool to find 2-3 pieces of relevant information on the given topic and present the findings with citations.""",
    tools=[google_search],
    output_key="research_findings",  # The result of this agent will be stored in the session state with this key.
)

print(" 2. research_agent created.")

summarize_agent = Agent(
    name="SummarizeAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Read the provided research findings: {research_findings}
        Create a concise summary as a bulleted list with 3-5 key points.""",
    output_key="final_summary",
)
print(" 3. summarize_agent created.")

# Root Coordinator: Orchestrates the workflow by calling the sub-agents as tools
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    instruction="""You are a research coordinator. Your goal is to answer the user's query by orchestrating a workflow.
    1. First, you MUST call the `ResearchAgent` tool find relevant information on the given topic provided by the user.
    2. Next, after receiving the research findings, you MUST call the `SummarizeAgent` tool to create a concise summary. 
    3. Finally, present the final summary clearly to the user as your response.
    """,
    tools=[AgentTool(research_agent), AgentTool(summarize_agent)],
)
print("4. root_agent created.")


async def run():
    runner = InMemoryRunner(agent=root_agent)
    print(f'runner defined1.{runner}')
    user_prompt = "What are the latest advancements in quantum computing and what do they mean for AI?"
    response = await runner.run_debug([user_prompt])


if __name__ == "__main__":
    asyncio.run(run())

    # we can create agent using adk library






