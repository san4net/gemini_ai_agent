import asyncio

from google.adk.cli.built_in_agents.agent import root_agent

import utils

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool


# import os
# from kaggle_secrets import UserSecretsClient

GOOGLE_API_KEY='AQ.Ab8RN6Lud5xZ2-c_iGETQnz3ExvlX7hel3vo1MVBWtxLAAxIKw'
# os.environ.setdefault('GOOGLE_API_KEY', GOOGLE_API_KEY)
utils.configure_api_key(GOOGLE_API_KEY)
retry_config = utils.retry_config()
model_llm ='gemini-3.5-flash-lite'

outline_agent = Agent(
    name="OutlineAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Create a blog outline for the given topic with:
    1. A catchy headline
    2. An introduction hook
    3. 3-5 main sections with 2-3 bullet points for each
    4. A concluding thought""",
    output_key="blog_outline",  # The result of this agent will be stored in the session state with this key.
)
print('outline agent created')
# Writer Agent: Writes the full blog post based on the outline from the previous agent.
writer_agent = Agent(
    name="WriterAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    # The `{blog_outline}` placeholder automatically injects the state value from the previous agent's output.
    instruction="""Following this outline strictly: {blog_outline}
    Write a brief, 200 to 300-word blog post with an engaging and informative tone.""",
    output_key="blog_draft",  # The result of this agent will be stored with this key.
)
print('writer agent created')

# Editor Agent: Edits and polishes the draft from the writer agent.
editor_agent = Agent(
    name="EditorAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    # This agent receives the `{blog_draft}` from the writer agent's output.
    instruction="""Edit this draft: {blog_draft}
    Your task is to polish the text by fixing any grammatical errors, improving the flow and sentence structure, and enhancing overall clarity.""",
    output_key="final_blog",  # This is the final output of the entire pipeline.
)
print('editor_agent created')

root_agent = SequentialAgent(
    name="BlogPipeline",
    sub_agents=[outline_agent, writer_agent, editor_agent],
)
print('sequential agent created')

async def run():
    runner = InMemoryRunner(agent=root_agent)
    print(f'runner defined1.{runner}')
    user_prompt = "Write a blog post about the benefits of multi-agent systems for software developers"
    response = await runner.run_debug([user_prompt])


if __name__ == "__main__":
    asyncio.run(run())

    # we can create agent using adk library






