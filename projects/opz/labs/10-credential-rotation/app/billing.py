"""Billing service. Logs in to the db on every request."""

from common import db_login, read_password, serve


def health() -> bool:
    return db_login(read_password())


if __name__ == "__main__":
    serve("billing", health)
