# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r ./backend/requirements.txt
COPY ./backend/app.py .
COPY ./backend/pok_curriculum_trimmed.json .

EXPOSE 5000

CMD ["python", "app.py"]