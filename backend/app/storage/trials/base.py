from abc import ABC, abstractmethod

from app.domain import Trial, TrialStatus


class TrialRepository(ABC):
    """Persistence port for trials."""

    async def start(self) -> None:  # noqa: B027 - optional hook
        """Open connections / create the schema. Called once at startup."""

    async def close(self) -> None:  # noqa: B027 - optional hook
        """Release resources. Called once at shutdown."""

    @abstractmethod
    async def save(self, trial: Trial) -> None:
        """Insert or update ``trial``, segments included."""

    @abstractmethod
    async def get(self, trial_id: str) -> Trial | None: ...

    @abstractmethod
    async def find(
        self, search: str | None = None, status: TrialStatus | None = None
    ) -> list[Trial]:
        """Newest first. ``search`` matches the title or the subject's name, ignoring case."""


def matches(trial: Trial, search: str | None, status: TrialStatus | None) -> bool:
    """Reference semantics of :meth:`TrialRepository.find` filters."""
    if status is not None and trial.status != status:
        return False
    if search:
        haystack = f"{trial.title}\n{trial.subject.name or ''}".casefold()
        return search.casefold() in haystack
    return True
