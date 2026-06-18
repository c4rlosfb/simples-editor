# Backend runtime — Ubuntu 24.04 + toolchain SIMPLES
# Referência: PRD §14.3
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nasm \
    binutils-i686-linux-gnu \
    python3 python3-venv python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/venv/bin:$PATH"

# Build simplesc: compile from source if available, otherwise create mock
# (Unified with Dockerfile.demo — both use build_simplesc.sh)
COPY build_simplesc.sh /tmp/
COPY simples-compiler/ /app/simples-compiler/
RUN bash /tmp/build_simplesc.sh && rm /tmp/build_simplesc.sh

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
