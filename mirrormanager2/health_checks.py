from flask_healthz import HealthError
from sqlalchemy_helpers import DatabaseStatus

from mirrormanager2.database import DB


def liveness():
    pass


def readiness():
    try:
        status = DB.manager.get_status()
    except Exception as e:
        raise HealthError(f"Can't get the database status: {e}") from e
    if status is DatabaseStatus.NO_INFO:
        raise HealthError("Can't connect to the database")
    if status is DatabaseStatus.UPGRADE_AVAILABLE:
        raise HealthError("The database schema needs to be updated")
