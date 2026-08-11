FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

USER pwuser
ENTRYPOINT ["xvfb-run", "-a", "geo-monitor"]
