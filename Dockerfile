FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y net-tools
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
