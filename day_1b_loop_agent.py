import asyncio

from google.adk.agents.callback_context import CallbackContext
from google.adk.cli.built_in_agents.agent import root_agent

import utils

from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LlmAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool, ToolContext

# import os
# from kaggle_secrets import UserSecretsClient

utils.configure_api_key()
retry_config = utils.retry_config()
model_llm = 'gemini-3.5-flash-lite'
# --- State Keys ---
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
# Define the exact phrase the Critic should use to signal completion
COMPLETION_PHRASE = "No major issues found."

# --- Before Agent Callback ---
def update_initial_topic_state(callback_context: CallbackContext):
    """Ensure 'initial_topic' is set in state before pipeline starts."""
    callback_context.state['initial_topic'] = callback_context.state.get('initial_topic', 'a robot developing unexpected emotions')

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}

# initial prompt - writer agent [story]-> critic agent [critic]->  iteratio<max & not approved -> iterate else finish
initial_writer_agent=LlmAgent(
name='InitialWriterAgent',
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    include_contents= 'none',
    instruction=
    f'''
you are creative writing assistant tasked with starting a story.
Write a very basic story first draft of story (just 1-2 simple sentences)
Keep it plain and minimal do not add descriptive.
Topic: {{initial_topic}}
Output *only* the story/document text. Do not add introductions or explanations.
''',
description="Writes the initial document draft based on the topic, aiming for some initial substance.",
output_key=STATE_CURRENT_DOC
)

critic_agent_in_loop = LlmAgent(
    name='CriticAgent',
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
include_contents='none',
    instruction=f"""
    You are a Constructive Critic AI reviewing a short story draft.

    **Document to Review:**
    ```
    {{current_document}}
    ```

    **Completion Criteria (ALL must be met):**
    1. At least 4 sentences long
    2. Has a clear beginning, middle, and end
    3. Includes at least one descriptive detail (sensory or emotional)

    **Task:**
    Check the document against the criteria above.

    IF any criteria is NOT met, provide specific feedback on what to add or improve.
    Output *only* the critique text.

    IF ALL criteria are met, respond *exactly* with: "{COMPLETION_PHRASE}"
    """,
    description="Reviews the current draft, providing critique if clear improvements are needed, otherwise signals completion.",
    output_key=STATE_CRITICISM
)
# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    # Relies solely on state via placeholders
    include_contents='none',
    instruction=f"""
    You are a Creative Writing Assistant refining a document based on feedback OR exiting the process.
    **Current Document:**
    ```
    {{current_document}}
    ```
    **Critique/Suggestions:**
    {{criticism}}

    **Task:**
    Analyze the 'Critique/Suggestions'.
    IF the critique is *exactly* "{COMPLETION_PHRASE}":
    You MUST call the 'exit_loop' function. Do not output any text.
    ELSE (the critique contains actionable feedback):
    Carefully apply the suggestions to improve the 'Current Document'. Output *only* the refined document text.

    Do not add explanations. Either output the refined document OR call the exit_loop function.
    """,
    description="Refines the document based on critique, or calls exit_loop if critique indicates completion.",
    tools=[exit_loop], # Provide the exit_loop tool
    output_key=STATE_CURRENT_DOC # Overwrites state['current_document'] with the refined version
)

agent_in_loop = LoopAgent(
    name="RefinementLoop",
    sub_agents=[critic_agent_in_loop,refiner_agent_in_loop],
    max_iterations= 3,
)
# orchestrating with initial writer and then refined with help of critic and refiner
root_agent = SequentialAgent(
    name="IterativeWritingPipeline",
    sub_agents=[initial_writer_agent,agent_in_loop],
    before_agent_callback=update_initial_topic_state,
    description="Writes an initial document and then iteratively refines it with critique using an exit tool.",
)

async def run():
    runner = InMemoryRunner(agent=root_agent)
    print(f'runner defined1.{runner}')
    user_prompt = "Write a short story about a lighthouse keeper who discovers a mysterious, glowing map"
    response = await runner.run_debug([user_prompt])
    print(response)


if __name__ == "__main__":
    asyncio.run(run())

    # we can create agent using adk library
