from alembic import command

from mirrormanager2.database import DB


def test_healthz_readiness_ok(client, db):
    result = client.get("/healthz/ready")
    assert result.status_code == 200


def test_healthz_readiness_not_ok_when_old_schema(client, db):
    command.downgrade(DB.manager.alembic_cfg, "-1")

    result = client.get("/healthz/ready")
    assert result.status_code != 200
    assert "The database schema needs to be updated" in result.get_data(as_text=True)


def test_healthz_readiness_not_ok(client):
    result = client.get("/healthz/ready")
    assert result.status_code != 200
