FROM debian:stable-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gawk \
        jq \
        wget \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /mnt
