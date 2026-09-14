FROM alpine:latest
WORKDIR /app

COPY . .

RUN apk add --no-cache python3 py3-pip
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

CMD ["python3", "main.py"]