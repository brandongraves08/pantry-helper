"""Add the separate prepping gear register."""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # main.py runs Base.metadata.create_all() during app startup before the
    # deploy script invokes Alembic. If that startup already created this new
    # model table, keep its data and let Alembic advance the revision.
    if sa.inspect(op.get_bind()).has_table("prepping_gear"):
        return

    op.create_table(
        "prepping_gear",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("condition", sa.String(), nullable=False, server_default=sa.text("'Unknown'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("prepping_gear")
