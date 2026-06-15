FROM python:3.12-slim

# Install binutils for i686 linking (nasm + ld)
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils-i686-linux-gnu \
    nasm \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled simplesc binary
COPY simplesc /usr/local/bin/simplesc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
