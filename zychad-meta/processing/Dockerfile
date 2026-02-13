FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Bot serves on port 5000, bind to 0.0.0.0 for Docker
ENV PORT=5000
EXPOSE 5000
CMD ["python", "zychad_metaV15.py"]
