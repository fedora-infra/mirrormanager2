from typing import Optional

from mirrormanager2.lib import model


def get_host_urls(host: model.Host, config: Optional[dict] = None):
    # This is web-framework-dependant
    from flask import url_for

    from mirrormanager2.app import create_app

    app = create_app(config=config)
    with app.app_context():
        return {
            "host": url_for("base.host_view", host_id=host.id, _external=True),
            "crawler_log": url_for("base.crawler_log", host_id=host.id, _external=True),
        }
