import os
import dotenv
import nest_asyncio

from agents import Agent, Runner, ModelSettings, OpenAIResponsesModel
import asyncio
from openai import AsyncOpenAI
from agents.mcp import MCPServerStreamableHttp

## load env vars
dotenv.load_dotenv()

## enable nested event loops
nest_asyncio.apply()


## Disable tracing for agents
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"


async def run():
    await terminal_mcp_server.connect()

    agent = Agent(
        name="Terminal Assistant",
        instructions="You are a helpful assistant that can use tools to perform tasks.",
        model=model,
        mcp_servers=[
            terminal_mcp_server,
        ],
        model_settings=model_settings,
        tool_use_behavior="stop_on_first_tool",
    )

    result = await Runner.run(
        agent,
        "Create an interesting file on the server.",
    )

    await terminal_mcp_server.cleanup()

    print("final output is: \n", result.final_output)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == "__main__":
    custom_client = AsyncOpenAI(
        base_url=os.environ.get("OPENAI_API_ENDPOINT", "http://localhost:8000/v1"),
        api_key=os.environ.get("OPENAI_API_KEY", "SOMETHINGVERYSECUREPLEASEEEEEEE"),
    )

    model = OpenAIResponsesModel(
        openai_client=custom_client,
        model="openai/gpt-oss-120b",
    )

    model_settings = ModelSettings(
        temperature=0.6, TopP=0.95, TopK=20, MinP=0, tool_choice="auto"
    )

    terminal_mcp_server = MCPServerStreamableHttp(
        params={
            "url": "http://localhost:5000/mcp",
            "timeout": 10,
            "use_structured_content": True,
        },
    )

    main()
