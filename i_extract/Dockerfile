FROM python:3.10-slim

WORKDIR /app

RUN apt-get update -qq && apt-get install -y -qq \
    libxcb1 libxcb-shm0 libxcb-xfixes0 libxcb-shape0 \
    libgl1 libgomp1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install opencv-python-headless --force-reinstall --no-deps

COPY . .

RUN mkdir -p /app/knowledge/samples /app/static/uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "app.main:app"]
