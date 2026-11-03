#!/usr/bin/env bash
set -euo pipefail

# Expand ~ explicitly (important in non-interactive shells)
source ~/Envs/quarto/bin/activate




quarto preview index.qmd


