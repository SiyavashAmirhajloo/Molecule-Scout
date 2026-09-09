"""known_molecules table + vector extension."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "known_molecules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_smiles", sa.Text(), nullable=False, unique=True),
        sa.Column("chembl_id", sa.String(32)),
        sa.Column("name", sa.Text()),
        sa.Column("fingerprint", Vector(2048), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("known_molecules")
