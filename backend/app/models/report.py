from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.molecule import Base


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        # One report per run. A concurrent duplicate insert fails loud instead
        # of silently duplicating (the V7 atomic-resume discipline).
        UniqueConstraint("project_id", "pipeline_run_id", name="uq_report_run"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"))
    payload_json: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(64), default="template-fallback")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
