from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.molecule import Base


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    __table_args__ = (
        # Starring the same molecule twice is a no-op, not a duplicate row.
        UniqueConstraint("project_id", "candidate_smiles", name="uq_shortlist_candidate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    docking_result_id: Mapped[int | None] = mapped_column(ForeignKey("docking_results.id"))
    candidate_smiles: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
