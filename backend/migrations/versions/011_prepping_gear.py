"""Add the separate prepping gear register."""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # main.py runs Base.metadata.create_all() during app startup before the
    # deploy script invokes Alembic. IF NOT EXISTS makes this safe both for
    # that normal sequence and if app startup races the migration.
    gear_table = sa.Table(
        "prepping_gear",
        sa.MetaData(),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column(
            "condition",
            sa.String(),
            nullable=False,
            server_default=sa.text("'Unknown'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(sa.schema.CreateTable(gear_table, if_not_exists=True))


def downgrade() -> None:
    op.drop_table("prepping_gear")
