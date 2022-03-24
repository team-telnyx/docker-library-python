FROM debian:stable-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gawk \
        jq \
        wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /mnt
