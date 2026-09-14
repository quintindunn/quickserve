"""
Main entry point for quickserve

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging
import sys

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    from QuickServe.Database import db, connect, MODELS
    from QuickServe.Web import create_app
    from QuickServe.FileSystem import config

    connect()
    db.create_tables(MODELS)

    app = create_app(config)
    app.run(host="0.0.0.0", port=8080, debug=True)
