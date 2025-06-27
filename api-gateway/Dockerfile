# Use official Python image
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7999

HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=5 CMD curl -I http://localhost:7999/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7999"]

