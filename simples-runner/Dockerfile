# Minimal sandbox image for running compiled i686 binaries
# Uses qemu-user-static to emulate x86 on ARM64 hosts (e.g. Oracle Ampere)
FROM alpine:3.21

RUN apk add --no-cache qemu-user-static

# Create sandbox user (nobody equivalent)
RUN adduser -D -u 65534 sandbox

WORKDIR /sandbox
USER sandbox

# The compiled binary is mounted at /sandbox/programa (read-only)
# qemu-i386-static emulates the x86 binary
ENTRYPOINT ["/usr/bin/qemu-i386-static", "/sandbox/programa"]
