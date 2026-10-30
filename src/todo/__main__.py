"""Entry point: python -m todo."""

import sys

from todo.cli import run

if __name__ == "__main__":  # pragma: no cover
    sys.exit(run(input, print))
