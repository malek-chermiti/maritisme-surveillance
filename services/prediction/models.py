import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Double, Index, Integer, PrimaryKeyConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class PredictionsLog(Base):
    __tablename__ = 'predictions_log'
    __table_args__ = (
        CheckConstraint('anomaly_score >= 0::double precision AND anomaly_score <= 1::double precision', name='chk_anomaly_score'),
        PrimaryKeyConstraint('id', name='predictions_log_pkey'),
        Index('idx_predictions_log_created_at', 'created_at'),
        Index('idx_predictions_log_mmsi', 'mmsi')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pred_latitude: Mapped[float] = mapped_column(Double(53), nullable=False)
    pred_longitude: Mapped[float] = mapped_column(Double(53), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Double(53), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
