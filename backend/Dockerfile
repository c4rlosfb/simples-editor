# Toolchain cross-target i386 + Python 3.11
# Funciona em x86_64 (dev local) e ARM64 (Oracle Cloud Ampere A1)
# Referência: PRD §14.3
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nasm \
    binutils-i686-linux-gnu \
    python3.11 python3.11-venv python3-pip \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Symlink python3.11 como python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /venv && \
    /venv/bin/pip install -r requirements.txt
ENV PATH="/venv/bin:$PATH"
COPY . .

EXPOSE 5000
USER 65534:65534
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
