FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=1000

WORKDIR /app

COPY requirements.txt ./

# Install PyTorch first (CPU version from official index)
RUN pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu

# Then install other requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest_lbc.py ./

CMD ["python", "ingest_lbc.py"]
