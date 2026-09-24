"""PyInstaller entry point; ordinary launches open the desktop."""

import sys

from photonguard.gui import main

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from photonguard.smoke import run
        run(sys.argv[2])
    else:
        raise SystemExit(main())
