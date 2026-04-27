from __future__ import annotations
import sys
from pathlib import Path

# Garante que o diretório raiz esteja no path quando executado diretamente
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.app import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
