#!/bin/sh
set -eu

for package in A B C
do
    ./run_stage5.sh \
        --package "$package" \
        --repository tests/test-repository.txt \
        --test-mode \
        --max-depth 10
done
