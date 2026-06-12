import argparse

from app.cli.commands import register_all


def main():
    parser = argparse.ArgumentParser(description="Artisan-style CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_all(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
