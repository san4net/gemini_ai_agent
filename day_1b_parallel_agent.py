import asyncio

from google.adk.cli.built_in_agents.agent import root_agent

import utils

from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool

# import os
# from kaggle_secrets import UserSecretsClient

utils.configure_api_key()
retry_config = utils.retry_config()
model_llm = 'gemini-3.5-flash-lite'

tech_research = Agent(
    name="TechResearchAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Research the latest AI/ML trends. Include 3 key developments,
    the main companies involved, and the potential impact. Keep the report very concise (100 words).""",
    tools=[google_search],
    output_key="tech_research",  # The result of this agent will be stored in the session state with this key.
)
print("TechResearch created.")
# Health Researcher: Focuses on medical breakthroughs.
health_researcher = Agent(
    name="HealthResearcher",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Research recent medical breakthroughs. Include 3 significant advances,
their practical applications, and estimated timelines. Keep the report concise (100 words).""",
    tools=[google_search],
    output_key="health_research",  # The result will be stored with this key.
)
print("HealthResearcher created.")

# Finance Researcher: Focuses on fintech trends.
finance_researcher = Agent(
    name="FinanceResearcher",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Research current fintech trends. Include 3 key trends,
their market implications, and the future outlook. Keep the report concise (100 words).""",
    tools=[google_search],
    output_key="finance_research",  # The result will be stored with this key.
)

print("finance_researcher created.")

aggregator_agent = Agent(
    name="AggregatorAgent",
    model=Gemini(
        model=model_llm,
        retry_options=retry_config
    ),
    instruction="""Combine these three research findings into a single executive summary:

    **Technology Trends:**
    {tech_research}
    
    **Health Breakthroughs:**
    {health_research}
    
    **Finance Innovations:**
    {finance_research}
    
    Your summary should highlight common themes, surprising connections, and the most important key takeaways from all three reports. The final summary should be around 200 words.""",
    output_key="executive_summary",
)
print("Aggregator created.")

parallel_research_team = ParallelAgent(
    name="ParallelResearchTeam",
    sub_agents=[tech_research, health_researcher, finance_researcher, ],
)
print("ParallelResearch created.")

root_agent = SequentialAgent(
    name="ResearchSystem",
    sub_agents=[parallel_research_team, aggregator_agent],
)

print('parallel research and sequential stitching done')

async def run():
    runner = InMemoryRunner(agent=root_agent)
    print(f'runner defined1.{runner}')
    user_prompt = "Run the daily executive briefing on Tech, Health, and Finance"
    response = await runner.run_debug([user_prompt])


if __name__ == "__main__":
    asyncio.run(run())

    # we can create agent using adk library
