"""reports + shortlist_items tables."""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "pipeline_run_id", sa.Integer(), sa.ForeignKey("pipeline_runs.id"), nullable=False
        ),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("model", sa.String(64), server_default="template-fallback"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "pipeline_run_id", name="uq_report_run"),
    )
    op.create_table(
        "shortlist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("docking_result_id", sa.Integer(), sa.ForeignKey("docking_results.id")),
        sa.Column("candidate_smiles", sa.Text(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "candidate_smiles", name="uq_shortlist_candidate"),
    )


def downgrade() -> None:
    op.drop_table("shortlist_items")
    op.drop_table("reports")
