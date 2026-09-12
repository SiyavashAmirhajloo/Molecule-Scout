from typing import Protocol


class GeneratorBackend(Protocol):
    name: str

    def generate(
        self,
        n: int,
        mw_range: tuple[float, float] | None = None,
        logp_range: tuple[float, float] | None = None,
        seed: int | None = None,
    ) -> list[str]: ...
