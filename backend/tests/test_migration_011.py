from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from app.db.models import PreppingGear


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


def test_revision_011_is_safe_when_startup_create_all_already_created_gear(
    tmp_path, monkeypatch
):
    """The app's startup create_all may create gear before Alembic upgrades."""
    database = tmp_path / "revision-010-with-created-gear.sqlite"
    url = f"sqlite:///{database}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('010')")
        )

    # Mirror Base.metadata.create_all() having created the new model table before
    # deploy.sh reaches `alembic upgrade head`.
    PreppingGear.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO prepping_gear "
                "(id, name, category, quantity, condition) "
                "VALUES ('existing-gear', 'Water filter', 'water', 1, 'Good')"
            )
        )

    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "011")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT id, name FROM prepping_gear")).all() == [
            ("existing-gear", "Water filter")
        ]
        assert (
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            == "011"
        )
    engine.dispose()
