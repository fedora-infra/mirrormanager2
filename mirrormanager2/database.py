from sqlalchemy_helpers.flask_ext import DatabaseExtension

from mirrormanager2.lib.database import BASE

DB = DatabaseExtension(base_model=BASE)
