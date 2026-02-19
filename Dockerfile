FROM dhi.io/python:3.11-debian13-sfw-dev

COPY ./py-agterm /py-agterm

RUN ["sfw", "pip", "install", "/py-agterm"]

RUN ["rm", "-rf", "py-agterm"]

RUN ["sfw", "pip", "install", "mcp"]

COPY ./terminal_mcp_server.py /app/terminal_mcp_server.py

WORKDIR /app

ENTRYPOINT [ "python", "terminal_mcp_server.py"  ]