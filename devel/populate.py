#!/usr/bin/env python3

from sqlalchemy.exc import IntegrityError

from mirrormanager2.app import create_app
from mirrormanager2.database import DB
from tests import conftest

app = create_app()

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
with app.app_context():
    DB.manager.sync()
    print("Database schema created")
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
