import sqlalchemy as sa
from sqlalchemy_helpers import DatabaseManager, get_base


class MirrorManagerBaseMixin:
    """Base mixin for mirrormanager2 models.

    This base class mixin grants sqlalchemy models dict-like access so that
    they behave somewhat similarly to SQLObject models (inherited from the TG1
    codebase of mirrormanager1).  This was added with the intent to make the
    porting of backend scripts from mirrormanager1 to mirrormanager2 easier.
    """

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)

    @classmethod
    def get(cls, session, pkey_value):
        primary_keys = [key.key for key in cls.__mapper__.primary_key]
        return (
            session.query(cls)
            .filter(sa.or_(getattr(cls, col) == pkey_value for col in primary_keys))
            .one()
        )


BASE = get_base(cls=MirrorManagerBaseMixin)


def get_db_manager(config, **engine_args):
    uri = config["SQLALCHEMY_DATABASE_URI"]
    alembic_location = config["DB_ALEMBIC_LOCATION"]
    return DatabaseManager(uri, alembic_location, engine_args=engine_args, base_model=BASE)
