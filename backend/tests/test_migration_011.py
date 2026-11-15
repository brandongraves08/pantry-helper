from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_revision_011_adds_only_gear_and_preserves_revision_010_data(
    tmp_path, monkeypatch
):
    database = tmp_path / "revision-010.sqlite"
    url = f"sqlite:///{database}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('010')")
        )
        connection.execute(
            text(
                "CREATE TABLE inventory_flags (id TEXT PRIMARY KEY, reason TEXT NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO inventory_flags (id, reason) VALUES ('sentinel-flag', 'preserve me')"
            )
        )
        original_tables = set(inspect(connection).get_table_names())

    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "011")

    with engine.connect() as connection:
        upgraded = inspect(connection)
        assert set(upgraded.get_table_names()) == original_tables | {"prepping_gear"}
        assert connection.execute(
            text("SELECT id, reason FROM inventory_flags")
        ).all() == [("sentinel-flag", "preserve me")]
        assert (
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            == "011"
        )

    command.downgrade(config, "010")

    with engine.connect() as connection:
        downgraded = inspect(connection)
        assert set(downgraded.get_table_names()) == original_tables
        assert connection.execute(
            text("SELECT id, reason FROM inventory_flags")
        ).all() == [("sentinel-flag", "preserve me")]
        assert (
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            == "010"
        )
    engine.dispose()
