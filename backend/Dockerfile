# ============================================================
# Stage 1: Build simplesc from source
# ============================================================
FROM ubuntu:22.04 AS simplesc-builder

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /simplesc
RUN git clone https://github.com/c4rlosfb/simples-compiler.git . \
    && make build/simplesc \
    && cp build/simplesc /usr/local/bin/simplesc

# ============================================================
# Stage 2: Backend runtime
# ============================================================
FROM python:3.12-slim

# Install binutils for i686 linking (nasm + ld)
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils-i686-linux-gnu \
    nasm \
    && rm -rf /var/lib/apt/lists/*

# Copy simplesc from builder stage
COPY --from=simplesc-builder /usr/local/bin/simplesc /usr/local/bin/simplesc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
