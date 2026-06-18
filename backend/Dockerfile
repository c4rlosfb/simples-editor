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

# Copy pre-built simplesc binary (compiled from simples-compiler repo)
COPY simples-compiler/build/simplesc /usr/local/bin/simplesc
RUN chmod +x /usr/local/bin/simplesc

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
