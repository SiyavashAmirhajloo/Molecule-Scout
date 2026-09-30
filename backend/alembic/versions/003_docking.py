"""docking_results table."""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "docking_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("candidate_smiles", sa.Text(), nullable=False),
        sa.Column("affinity", sa.Float()),
        sa.Column("qed", sa.Float()),
        sa.Column("novelty", sa.Float()),
        sa.Column("rank_score", sa.Float()),
        sa.Column("formula_version", sa.String(16), server_default="v6-1"),
        sa.Column("pose_pdbqt", sa.Text()),
        sa.Column("receptor_pdb_id", sa.String(16)),
        sa.Column("box_center_x", sa.Float()),
        sa.Column("box_center_y", sa.Float()),
        sa.Column("box_center_z", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("docking_results")
