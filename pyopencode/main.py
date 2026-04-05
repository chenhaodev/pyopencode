"""Console script entry: ``pyopencode``."""

from pyopencode.cli_entry import cli, dispatch_main, run_cli

# Re-export for tests and ``python -m pyopencode.main``.
__all__ = ["cli", "dispatch_main", "main", "run_cli"]


def main() -> None:
    dispatch_main()


if __name__ == "__main__":
    main()
