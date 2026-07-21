from typing import Optional
import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Double, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class ProtectedZones(Base):
    __tablename__ = 'protected_zones'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='protected_zones_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    center_lat: Mapped[float] = mapped_column(Double(53), nullable=False)
    center_lon: Mapped[float] = mapped_column(Double(53), nullable=False)
    radius_km: Mapped[float] = mapped_column(Double(53), nullable=False, server_default=text('5'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    description: Mapped[Optional[str]] = mapped_column(Text)

    alerts: Mapped[list['Alerts']] = relationship('Alerts', back_populates='zone')


class Alerts(Base):
    __tablename__ = 'alerts'
    __table_args__ = (
        CheckConstraint("alert_level::text = ANY (ARRAY['NORMAL'::character varying, 'WARNING'::character varying, 'CRITICAL'::character varying]::text[])", name='chk_alert_level'),
        CheckConstraint("alert_reason::text = ANY (ARRAY['INTRUSION'::character varying, 'DEGAZAGE'::character varying, 'LES_DEUX'::character varying]::text[])", name='chk_alert_reason'),
        CheckConstraint('anomaly_score IS NULL OR anomaly_score >= 0::double precision AND anomaly_score <= 1::double precision', name='chk_anomaly_score'),
        ForeignKeyConstraint(['zone_id'], ['protected_zones.id'], name='alerts_zone_id_fkey'),
        PrimaryKeyConstraint('id', name='alerts_pkey'),
        Index('idx_alerts_created_at', 'created_at'),
        Index('idx_alerts_mmsi', 'mmsi')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(10), nullable=False)
    alert_reason: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    zone_id: Mapped[Optional[int]] = mapped_column(Integer)
    distance_km: Mapped[Optional[float]] = mapped_column(Double(53))
    anomaly_score: Mapped[Optional[float]] = mapped_column(Double(53))

    zone: Mapped[Optional['ProtectedZones']] = relationship('ProtectedZones', back_populates='alerts')
