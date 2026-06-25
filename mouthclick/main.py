import argparse
import sys

if __package__:
    from . import __version__
    from .src.app import run
else:
    from __init__ import __version__
    from src.app import run


def build_parser():
    parser = argparse.ArgumentParser(
        prog="mouthclick",
        description="Controle de mouse por webcam usando nariz e gesto de lingua.",
    )
    parser.add_argument("--version", action="version", version=f"MouthClick {__version__}")
    return parser


def main(argv=None):
    parser = build_parser()
    parser.parse_args(argv)
    return run()


if __name__ == "__main__":
    sys.exit(main())
