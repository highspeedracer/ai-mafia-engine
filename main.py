"""Entry point for the Town of Salem clone."""
from engine import GameEngine


def main() -> None:
    engine = GameEngine()
    engine.run()


if __name__ == "__main__":
    main()
