import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum


class TrialStatus(StrEnum):
    CREATED = "created"
    """Created, data intake never started."""
    RECORDING = "recording"
    PAUSED = "paused"
    """Intake stopped, can be resumed."""
    COMPLETED = "completed"
    """Intake stopped for good, the trial is saved."""


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class TrialStateError(Exception):
    """An action is not allowed in the trial's current status."""


@dataclass(frozen=True, slots=True)
class Subject:
    """The person being tested. Everything is optional."""

    name: str | None = None
    age: int | None = None
    sex: Sex | None = None
    culture: str | None = None


@dataclass(frozen=True, slots=True)
class Segment:
    """One uninterrupted period of data intake from one device."""

    device_id: str
    started_at: datetime
    stopped_at: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.stopped_at is None


@dataclass(slots=True)
class Trial:
    """An experiment on a subject. Its data is whatever its device(s) sent during its segments.

    Status changes only go through the methods below, which enforce the life cycle::

        CREATED ──start──▶ RECORDING ──stop──▶ PAUSED ──start──▶ RECORDING ...
           └──────────────────┴──────complete────┴──▶ COMPLETED
    """

    title: str
    created_at: datetime
    description: str | None = None
    subject: Subject = field(default_factory=Subject)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: TrialStatus = TrialStatus.CREATED
    segments: list[Segment] = field(default_factory=list)
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        _check_title(self.title)

    def update_details(self, title: str, description: str | None, subject: Subject) -> None:
        """Descriptive information can be corrected at any time, even once completed."""
        _check_title(title)
        self.title, self.description, self.subject = title, description, subject

    @property
    def recording_device(self) -> str | None:
        """Device currently recorded, if any."""
        if self.segments and self.segments[-1].is_open:
            return self.segments[-1].device_id
        return None

    def start(self, device_id: str, now: datetime) -> None:
        self._require(TrialStatus.CREATED, TrialStatus.PAUSED, action="start")
        self.segments.append(Segment(device_id, started_at=now))
        self.status = TrialStatus.RECORDING

    def stop(self, now: datetime) -> None:
        self._require(TrialStatus.RECORDING, action="stop")
        self._close_segment(now)
        self.status = TrialStatus.PAUSED

    def complete(self, now: datetime) -> None:
        self._require(
            TrialStatus.CREATED, TrialStatus.RECORDING, TrialStatus.PAUSED, action="complete"
        )
        self._close_segment(now)
        self.status = TrialStatus.COMPLETED
        self.completed_at = now

    def _close_segment(self, now: datetime) -> None:
        if self.segments and self.segments[-1].is_open:
            self.segments[-1] = replace(self.segments[-1], stopped_at=now)

    def _require(self, *allowed: TrialStatus, action: str) -> None:
        if self.status not in allowed:
            raise TrialStateError(f"Cannot {action} a trial that is {self.status}")


def _check_title(title: str) -> None:
    if not title.strip():
        raise ValueError("Trial title must not be empty")
