from typing import Optional
import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Double, Index, Integer, PrimaryKeyConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class SimulationZone(Base):
    __tablename__ = 'simulation_zone'
    __table_args__ = (
        CheckConstraint('lat_min < lat_max', name='chk_lat_order'),
        CheckConstraint('lon_min < lon_max', name='chk_lon_order'),
        PrimaryKeyConstraint('id', name='simulation_zone_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lat_min: Mapped[float] = mapped_column(Double(53), nullable=False)
    lat_max: Mapped[float] = mapped_column(Double(53), nullable=False)
    lon_min: Mapped[float] = mapped_column(Double(53), nullable=False)
    lon_max: Mapped[float] = mapped_column(Double(53), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class VesselPositions(Base):
    __tablename__ = 'vessel_positions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='vessel_positions_pkey'),
        Index('idx_vessel_positions_mmsi', 'mmsi'),
        Index('idx_vessel_positions_recorded_at', 'recorded_at')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, nullable=False)
    latitude: Mapped[float] = mapped_column(Double(53), nullable=False)
    longitude: Mapped[float] = mapped_column(Double(53), nullable=False)
    recorded_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    speed: Mapped[Optional[float]] = mapped_column(Double(53))
    heading: Mapped[Optional[float]] = mapped_column(Double(53))
