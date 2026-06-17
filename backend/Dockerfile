# Backend runtime — Ubuntu 24.04 + toolchain SIMPLES
# Referência: PRD §14.3
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nasm \
    binutils-i686-linux-gnu \
    python3.11 python3.11-venv python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/venv/bin:$PATH"
COPY . .

EXPOSE 5000
USER 65534:65534
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
