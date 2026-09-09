from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class KnownMolecule(Base):
    __tablename__ = "known_molecules"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_smiles: Mapped[str] = mapped_column(Text, unique=True)
    chembl_id: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str | None] = mapped_column(Text)
    fingerprint: Mapped[list[float]] = mapped_column(Vector(2048))
