# ============================================================
# Backend runtime — compiles simplesc from source tarball
# ============================================================
FROM python:3.12-slim

# Install build tools and runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    binutils-i686-linux-gnu \
    nasm \
    && rm -rf /var/lib/apt/lists/*

# Download and compile simplesc from stable tarball (no git clone)
ADD https://github.com/c4rlosfb/simples-compiler/archive/main.tar.gz /simplesc/
RUN cd /simplesc/* && make build/simplesc && cp build/simplesc /usr/local/bin/simplesc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]
