FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY birthday_bot ./birthday_bot
ENV DATABASE_PATH=/app/data/birthdays.sqlite3
CMD ["python", "-m", "birthday_bot"]
