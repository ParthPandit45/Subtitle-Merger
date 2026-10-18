"""Entry point when executed as a module (python -m merge_subs)."""

import sys
from merge_subs.cli import main

if __name__ == "__main__":
    sys.exit(main())
