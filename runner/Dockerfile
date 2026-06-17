# simples-runner — sandbox image for executing compiled SIMPLES binaries
#
# Uses Ubuntu 24.04 and includes qemu-user-static for ARM64 hosts
# (Oracle Ampere A1) to run x86 32-bit ELF binaries.
#
# Build reference: docker-compose.yml runner_image_build service.
# PRD §7.3.5 Sandbox container

FROM ubuntu:24.04

# Install runtime dependencies and qemu-user-static for ARM64→x86 emulation
RUN apt-get update && apt-get install -y --no-install-recommends \
    qemu-user-static \
    libc6-i386 \
    && rm -rf /var/lib/apt/lists/*

# Run as nobody
USER 65534:65534

# Default: keep alive briefly so the host can exec into the container;
# the actual binary is passed via docker exec in the backend.
CMD ["sleep", "infinity"]
