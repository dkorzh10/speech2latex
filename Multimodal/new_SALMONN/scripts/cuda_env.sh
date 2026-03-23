#!/usr/bin/env bash
# PyTorch pip wheels ship CUDA libs under site-packages/nvidia/*/lib.
# If you see libcudnn / libnvToolsExt / libcurand import errors, run:
#   source scripts/cuda_env.sh
# from the new_SALMONN directory (or set VENV_ROOT to your .venv).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_ROOT="${VENV_ROOT:-$ROOT/.venv}"
SP="$("$VENV_ROOT/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
export LD_LIBRARY_PATH="$SP/torch/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
for d in "$SP"/nvidia/*/lib; do
  if [[ -d "$d" ]]; then
    export LD_LIBRARY_PATH="$d:$LD_LIBRARY_PATH"
  fi
done
