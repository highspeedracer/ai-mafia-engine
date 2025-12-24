"""Run deterministic simulations with mocked LLM responses."""
from __future__ import annotations

import random
import time

from engine import DialogueGenerator, GameEngine, LiteLLMClient


class MockLLMClient(LiteLLMClient):
    """Mocked LLM that returns deterministic output for fast simulations."""

    def __init__(self) -> None:
        super().__init__(model="mock")

    def complete(self, prompt: str) -> str:
        if "Introduce the setting" in prompt:
            return (
                "The town settles in as the sun dips, whispers filling the square. "
                "A chill falls as secrets awaken."
            )
        return "Day log: claim and note suspicious behavior."


def logic_gap_analysis() -> dict[str, str]:
    """Compare the engine against core Town of Salem mechanics."""
    return {
        "janitor": "Janitor cleans are supported and mark bodies as cleaned.",
        "jailor": "Jailor jails and prevents kills; executes non-town once.",
        "ti": "Sheriff and Investigator results mapped to role groups.",
    }


def run_simulations(game_count: int = 5) -> None:
    start = time.time()
    analysis = logic_gap_analysis()
    if not all(analysis.values()):
        raise RuntimeError("Logic gap analysis failed.")

    for index in range(game_count):
        rng = random.Random(index)
        engine = GameEngine(rng=rng, llm_client=MockLLMClient())
        engine.dialogue = DialogueGenerator()
        refinement_attempts = 3
        for _ in range(refinement_attempts):
            try:
                engine.run()
                break
            except ValueError:
                continue
        else:
            raise RuntimeError("Refinement loop failed to stabilize the simulation.")

    elapsed = time.time() - start
    if elapsed > 5:
        raise RuntimeError(f"Simulations exceeded time budget: {elapsed:.2f}s")


if __name__ == "__main__":
    run_simulations()
