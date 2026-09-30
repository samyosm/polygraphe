from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, TypeDecorator, func, or_, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain import Segment, Sex, Subject, Trial, TrialStatus
from app.storage.trials.base import TrialRepository


class UTCDateTime(TypeDecorator[datetime]):
    """Stores aware datetimes as UTC. SQLite drops time zones, so they are re-attached on load."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        return value.astimezone(UTC).replace(tzinfo=None) if value else None

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return value.replace(tzinfo=UTC) if value else None


class Base(DeclarativeBase):
    pass


class TrialRow(Base):
    __tablename__ = "trials"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    subject_name: Mapped[str | None] = mapped_column(String(200))
    subject_age: Mapped[int | None]
    subject_sex: Mapped[str | None] = mapped_column(String(16))
    subject_culture: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    segments: Mapped[list["SegmentRow"]] = relationship(
        cascade="all, delete-orphan", order_by="SegmentRow.started_at", lazy="selectin"
    )


class SegmentRow(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trial_id: Mapped[str] = mapped_column(ForeignKey("trials.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    stopped_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class SqlTrialRepository(TrialRepository):
    """Trials in a SQL database (SQLite by default). The schema is created on startup."""

    def __init__(self, url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(url)
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def start(self) -> None:
        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self._engine.dispose()

    async def save(self, trial: Trial) -> None:
        async with self._sessions.begin() as session:
            row = await session.get(TrialRow, trial.id) or TrialRow(id=trial.id)
            _fill_row(row, trial)
            session.add(row)

    async def get(self, trial_id: str) -> Trial | None:
        async with self._sessions() as session:
            row = await session.get(TrialRow, trial_id)
            return _to_domain(row) if row else None

    async def find(
        self, search: str | None = None, status: TrialStatus | None = None
    ) -> list[Trial]:
        query = select(TrialRow).order_by(TrialRow.created_at.desc())
        if status is not None:
            query = query.where(TrialRow.status == status.value)
        if search:
            needle = search.lower()
            query = query.where(
                or_(
                    func.lower(TrialRow.title).contains(needle, autoescape=True),
                    func.lower(TrialRow.subject_name).contains(needle, autoescape=True),
                )
            )
        async with self._sessions() as session:
            return [_to_domain(row) for row in (await session.scalars(query)).all()]


def _fill_row(row: TrialRow, trial: Trial) -> None:
    row.title = trial.title
    row.description = trial.description
    row.subject_name = trial.subject.name
    row.subject_age = trial.subject.age
    row.subject_sex = trial.subject.sex.value if trial.subject.sex else None
    row.subject_culture = trial.subject.culture
    row.status = trial.status.value
    row.created_at = trial.created_at
    row.completed_at = trial.completed_at
    row.segments = [
        SegmentRow(device_id=s.device_id, started_at=s.started_at, stopped_at=s.stopped_at)
        for s in trial.segments
    ]


def _to_domain(row: TrialRow) -> Trial:
    return Trial(
        id=row.id,
        title=row.title,
        description=row.description,
        subject=Subject(
            name=row.subject_name,
            age=row.subject_age,
            sex=Sex(row.subject_sex) if row.subject_sex else None,
            culture=row.subject_culture,
        ),
        status=TrialStatus(row.status),
        created_at=row.created_at,
        completed_at=row.completed_at,
        segments=[Segment(s.device_id, s.started_at, s.stopped_at) for s in row.segments],
    )
