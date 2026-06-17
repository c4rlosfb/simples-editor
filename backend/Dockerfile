<<<<<<< HEAD
<<<<<<< HEAD
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
=======
FROM python:3.12-slim

# Install binutils for i686 linking (nasm + ld)
RUN apt-get update && apt-get install -y --no-install-recommends \
=======
# ============================================================
# Backend runtime — compiles simplesc from source tarball
# ============================================================
FROM python:3.12-slim

# Install build tools and runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
>>>>>>> origin/fix/issue-31
    binutils-i686-linux-gnu \
    nasm \
    && rm -rf /var/lib/apt/lists/*

<<<<<<< HEAD
# Copy pre-compiled simplesc binary
COPY simplesc /usr/local/bin/simplesc
=======
# Download and compile simplesc from stable tarball (no git clone)
ADD https://github.com/c4rlosfb/simples-compiler/archive/main.tar.gz /simplesc/
RUN cd /simplesc/* && make build/simplesc && cp build/simplesc /usr/local/bin/simplesc
>>>>>>> origin/fix/issue-31

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

<<<<<<< HEAD
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
>>>>>>> origin/fix/issue-21
=======
EXPOSE 5000
CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
>>>>>>> origin/fix/issue-31
