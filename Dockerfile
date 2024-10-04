FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV TZ=Australia/Melbourne

# Copy Pipfile and Pipfile.lock first to leverage Docker cache
COPY data/bq-results-20240829-041517-1724904953827.jsonl data/bq-results-20240829-041517-1724904953827.jsonl
COPY data/ground-truth-retrieval.csv data/ground-truth-retrieval.csv
COPY ["Pipfile", "Pipfile.lock", "./"]

# Install dependencies using pipenv
RUN pip install --no-cache-dir pipenv
RUN pipenv install --deploy --system --ignore-pipfile

# Copy your application code
COPY bio-ai-assistant .

# Copy the secret files
COPY .env /app/.env
COPY pacific-ethos-428312-n5-eb4864ff3add.json /app/pacific-ethos-428312-n5-eb4864ff3add.json

EXPOSE 5000

CMD ["pipenv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "app:app"]