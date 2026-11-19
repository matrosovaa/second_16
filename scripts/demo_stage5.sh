#!/bin/sh
set -eu

REPOSITORY="${REPOSITORY:-https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/}"
DEPTH="${DEPTH:-3}"

mkdir -p out
for package in alpine-base build-base openssh
do
    ./run_stage5.sh \
        --package "$package" \
        --repository "$REPOSITORY" \
        --max-depth "$DEPTH" \
        --output "out/$package.svg" \
        --compare-apk
done
