from typing import Protocol


class GeneratorBackend(Protocol):
    name: str

    def generate(
        self,
        n: int,
        mw_range: tuple[float, float] | None = None,
        logp_range: tuple[float, float] | None = None,
        seed: int | None = None,
        seed_smiles: str | None = None,
        noise_steps: int = 100,
    ) -> list[str]: ...
