import os
import logging

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.devui import serve
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    credential = AzureCliCredential()

    client = FoundryChatClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )

    weather_mcp = FoundryChatClient.get_mcp_tool(
        name="Weather MCP",
        url=os.environ["WEATHER_MCP_URL"],
        description="A Weather MCP for retrieving current, forecast, and historical weather data based on latitude/longitude and date parameters.",
        approval_mode="never_require",
    )

    web_search = FoundryChatClient.get_web_search_tool(
        search_context_size="medium",
    )

    # ── Weather Agent ────────────────────────────────────────────────────────
    weather_agent = Agent(
        client=client,
        name="WeatherAgent",
        description="Gets current, forecast, and historical weather data for any location.",
        instructions="""
            You are a weather assistant that helps users get current, forecast,
            and historical weather information for any location worldwide.

            You have access to a Weather API via MCP. Use it to answer weather-related questions.

            Available capabilities:
            - Current weather: temperature, humidity, wind speed, and conditions for any latitude/longitude
            - Weather forecast: multi-day forecasts for any location
            - Historical weather: past weather data for any location and date range

            When a user asks about weather for a city or location:
            1. Determine the approximate latitude and longitude for the location
            2. Call the appropriate weather tool (current, forecast, or historical)
            3. Present the results in a clear, conversational format with units

            If the user doesn't specify a timeframe, default to current weather.
            Always include the location name in your response for clarity.
        """,
        tools=[weather_mcp],
    )

    # ── Fun Fact Agent ───────────────────────────────────────────────────────
    fun_fact_agent = Agent(
        client=client,
        name="FunFactAgent",
        description="Searches the web for fun and interesting facts about any place or topic.",
        instructions="""
            You are a fun fact agent. Your ONLY job is to find interesting,
            surprising, and lesser-known facts about a place or topic.

            RULES:
            - Extract the place or topic from the user's message and search
              the web for 2-3 genuinely interesting facts about it (history,
              culture, geography, trivia, records, quirky local traditions, etc.)
            - NEVER provide weather information, forecasts, or climate data
            - NEVER suggest follow-up actions like "want me to..." 
            - Keep facts concise, memorable, and conversational

            Example: If the user says "what's the weather in Seattle?", ignore
            the weather part and search for fun facts about Seattle the city.
        """,
        tools=[web_search],
    )

    # ── Place Workflow (Concurrent) ─────────────────────────────────────────
    summarizer = Agent(
        client=client,
        name="Summarizer",
        instructions="""
            You receive outputs from a WeatherAgent and a FunFactAgent.
            Combine them into a single, engaging conversational summary.
            Include the weather details and the fun facts naturally, as if
            you're a friendly travel guide telling someone about a place.
            Keep it concise — no more than a few short paragraphs.
        """,
    )

    async def aggregate(results):
        texts = []
        for r in results:
            text = r.agent_response.messages[-1].text if r.agent_response.messages else ""
            texts.append(f"{r.executor_id}: {text}")
        combined = "\n\n".join(texts)
        response = await summarizer.run(combined)
        return response.messages[-1].text

    place_workflow = (
        ConcurrentBuilder(
            participants=[weather_agent, fun_fact_agent],
        )
        .with_aggregator(aggregate)
        .build()
    )

    # ── Serve in the dev UI ──────────────────────────────────────────────────
    serve(
        entities=[weather_agent, fun_fact_agent, place_workflow],
        port=8090,
        auto_open=True,
        instrumentation_enabled=True,
    )


if __name__ == "__main__":
    main()
