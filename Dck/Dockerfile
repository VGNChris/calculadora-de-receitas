FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistência do banco de dados (pasta instance)
VOLUME /app/instance

EXPOSE 5000

CMD ["python", "backend.py"]
