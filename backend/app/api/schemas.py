"""HTTP/WebSocket representations. Kept apart from the domain so the API can evolve alone."""

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain import FieldValue, Measurement, Segment, Sex, Stage, Subject, Trial, TrialStatus
from app.ingestion import ConnectedDevice

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]


class SubjectSchema(BaseModel):
    name: ShortText | None = None
    age: Annotated[int, Field(ge=0, le=150)] | None = None
    sex: Sex | None = None
    culture: ShortText | None = None

    @classmethod
    def from_domain(cls, subject: Subject) -> Self:
        return cls(name=subject.name, age=subject.age, sex=subject.sex, culture=subject.culture)

    def to_domain(self) -> Subject:
        return Subject(name=self.name, age=self.age, sex=self.sex, culture=self.culture)


class TrialDetails(BaseModel):
    """Editable information of a trial, used both to create and to update one."""

    model_config = ConfigDict(extra="forbid")

    title: ShortText
    description: LongText | None = None
    subject: SubjectSchema = Field(default_factory=SubjectSchema)


class SegmentOut(BaseModel):
    device_id: str
    started_at: datetime
    stopped_at: datetime | None

    @classmethod
    def from_domain(cls, segment: Segment) -> Self:
        return cls(
            device_id=segment.device_id,
            started_at=segment.started_at,
            stopped_at=segment.stopped_at,
        )


class TrialOut(BaseModel):
    id: str
    title: str
    description: str | None
    subject: SubjectSchema
    status: TrialStatus
    created_at: datetime
    completed_at: datetime | None
    recording_device: str | None
    segments: list[SegmentOut]

    @classmethod
    def from_domain(cls, trial: Trial) -> Self:
        return cls(
            id=trial.id,
            title=trial.title,
            description=trial.description,
            subject=SubjectSchema.from_domain(trial.subject),
            status=trial.status,
            created_at=trial.created_at,
            completed_at=trial.completed_at,
            recording_device=trial.recording_device,
            segments=[SegmentOut.from_domain(s) for s in trial.segments],
        )


class StartRecording(BaseModel):
    device_id: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


class MeasurementOut(BaseModel):
    """Also the payload of every message on the live websocket."""

    stage: Stage
    kind: str
    device_id: str
    timestamp: datetime
    fields: dict[str, FieldValue]

    @classmethod
    def from_domain(cls, stage: Stage, measurement: Measurement) -> Self:
        return cls(
            stage=stage,
            kind=measurement.kind,
            device_id=measurement.device_id,
            timestamp=measurement.timestamp,
            fields=dict(measurement.fields),
        )


class DeviceOut(BaseModel):
    id: str
    source: str

    @classmethod
    def from_domain(cls, device: ConnectedDevice) -> Self:
        return cls(id=device.id, source=device.source)


class OperatorSignIn(BaseModel):
    password: Annotated[str, StringConstraints(max_length=200)]


class OperatorSessionOut(BaseModel):
    token: str
    expires_at: datetime
