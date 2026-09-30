import copy

from app.domain import Trial, TrialStatus
from app.storage.trials.base import TrialRepository, matches


class InMemoryTrialRepository(TrialRepository):
    """Non-persistent repository, for tests and for running without a database."""

    def __init__(self) -> None:
        self._trials: dict[str, Trial] = {}

    async def save(self, trial: Trial) -> None:
        # Copies make this behave like a real database: callers never share state.
        self._trials[trial.id] = copy.deepcopy(trial)

    async def get(self, trial_id: str) -> Trial | None:
        trial = self._trials.get(trial_id)
        return copy.deepcopy(trial) if trial else None

    async def find(
        self, search: str | None = None, status: TrialStatus | None = None
    ) -> list[Trial]:
        found = [copy.deepcopy(t) for t in self._trials.values() if matches(t, search, status)]
        return sorted(found, key=lambda t: t.created_at, reverse=True)
