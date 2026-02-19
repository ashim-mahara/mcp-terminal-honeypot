# Terminal MCP Server Honeypot

## Overview

I wanted to explore `docker diff` so I made this simple honeypot for a typical terminal mcp server. Currently it only extracts file artifcats from the server. There is support for excluding paths and file extensions (simple not magic headers).

## Usage

### Environment Variables

You will need to first set some variables for your `.env` file like:

```dotenv
OPENAI_API_KEY=sometoken
OPENAI_API_ENDPOINT=http://localhost:8000/v1
```

I am using `gpt-oss-120b` as the model but you can change that in the `main.py`.

### Dependencies

Install the dependencies with:

```bash
uv sync
```

You should also make sure that [docker](https://docs.docker.com/engine/install/) is installed.

### Starting Honeypot

You can simply start the honeypot server with:

```bash
python main.py
```

> The mcp server listens on port 5000. The honeypot also creates a bridge network interface in docker.

Note that the honeypot server is only going to live for 30 seconds in the current configuration. You can change that in the `main.py` file.

### Simulate Agent

We prompt the agent to interact with the honeypot with the `agent.py` file.

```bash
python agent.py
```

It will output how the agent interacted with the honeypot.

> Right now the agent only interacts once with the honeypot but multiple interactions can be added.