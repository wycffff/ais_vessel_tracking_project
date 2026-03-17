from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class VesselTrack(Base):
    __tablename__ = 'vessel_track'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    sog: Mapped[float | None] = mapped_column(Float, nullable=True)
    cog: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    nav_stat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rot: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_acc: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raim: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    source_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    inserted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_vessel_track_mmsi_event_time', 'mmsi', 'event_time'),
    )


class VesselState(Base):
    __tablename__ = 'vessel_state'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    vessel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    call_sign: Mapped[str | None] = mapped_column(String(100), nullable=True)
    imo: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    vessel_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_event_time: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    sog: Mapped[float | None] = mapped_column(Float, nullable=True)
    cog: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    nav_stat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class VesselMetadata(Base):
    __tablename__ = 'vessel_metadata'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metadata_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    vessel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    call_sign: Mapped[str | None] = mapped_column(String(100), nullable=True)
    imo: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    vessel_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draught: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    inserted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('mmsi', 'metadata_timestamp', name='uq_vessel_metadata_mmsi_timestamp'),
    )
