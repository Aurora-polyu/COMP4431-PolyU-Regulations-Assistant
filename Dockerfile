# syntax=docker/dockerfile:1

# ---- Runtime ----
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf \
    RETRIEVAL_INDEX_DIR=/app/handbook-index \
    USER_DATA_DB=/app/userdata/user_data.sqlite

WORKDIR /app

# ---- Dependencies (cached until requirements.txt changes) ----
# Install CPU-only PyTorch first so sentence-transformers does not pull the
# much larger CUDA build. The later install sees torch as already satisfied.
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Code and handbook passages ----
COPY app.py mcp_server.py ./
COPY src/ src/
COPY scripts/ scripts/
COPY assets/ assets/
COPY .streamlit/ .streamlit/
COPY data/chunks.jsonl data/chunks.jsonl

# Build the search index now. This also downloads the embedding model into
# HF_HOME, so the running container needs no internet access for retrieval.
RUN python scripts/build_index.py --chunks data/chunks.jsonl --index-dir "$RETRIEVAL_INDEX_DIR"

# Chats and saved answers live here; mount a volume to keep them.
RUN mkdir -p /app/userdata
VOLUME /app/userdata

# ---- Configuration (MODEL_API_KEY, MODEL_NAME, MODEL_BASE_URL) is supplied at run time ----
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
