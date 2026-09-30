from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.molecule import Base


class DockingResult(Base):
    __tablename__ = "docking_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    candidate_smiles: Mapped[str] = mapped_column(Text)
    affinity: Mapped[float | None] = mapped_column(Float)
    qed: Mapped[float | None] = mapped_column(Float)
    novelty: Mapped[float | None] = mapped_column(Float)
    rank_score: Mapped[float | None] = mapped_column(Float)
    formula_version: Mapped[str] = mapped_column(String(16), default="v6-1")
    pose_pdbqt: Mapped[str | None] = mapped_column(Text)
    receptor_pdb_id: Mapped[str | None] = mapped_column(String(16))
    box_center_x: Mapped[float | None] = mapped_column(Float)
    box_center_y: Mapped[float | None] = mapped_column(Float)
    box_center_z: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
