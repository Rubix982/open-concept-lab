"""Reports service. Reading the secret file on every request felt wasteful,
so it's read once when the service starts."""

from common import db_login, read_password, serve

PASSWORD = read_password()


def health() -> bool:
    return db_login(PASSWORD)


if __name__ == "__main__":
    serve("reports", health)
