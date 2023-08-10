#!/usr/bin/env python

from sqlalchemy.exc import IntegrityError

from mirrormanager2.app import DB, create_app
from mirrormanager2.lib import model
from tests import conftest

app = create_app()
model.create_tables(app.config["DB_URL"], app.config.get("PATH_ALEMBIC_INI", None))
print("Database schema created")

# Call the fixtures directly. It's unsupported by Pytest so it may break.
fixtures = (
    "base_items",
    "site",
    "hosts",
    "location",
    "netblockcountry",
    "directory",
    "category",
    "hostcategory",
    "hostcategoryurl",
    "hostcategorydir",
    "hostcountry",
    "hostpeerasn",
    "hostnetblock",
    "categorydirectory",
    "version",
    "repository",
    "repositoryredirect",
)
for funcname in fixtures:
    func = getattr(conftest, funcname).__pytest_wrapped__.obj
    try:
        func(DB.session)
    except IntegrityError:
        DB.session.rollback()
        continue
    else:
        print(f"Inserting objects from {funcname}")
        DB.session.commit()
