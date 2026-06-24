import sys

if __package__:
    from .src.app import run
else:
    from src.app import run


if __name__ == "__main__":
    sys.exit(run())
