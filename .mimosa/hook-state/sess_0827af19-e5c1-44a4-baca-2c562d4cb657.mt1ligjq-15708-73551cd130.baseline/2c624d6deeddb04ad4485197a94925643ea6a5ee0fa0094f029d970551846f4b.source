"""db.py — اتصالِ ساده به Postgres با psycopg3 (connection per request)."""

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def conn():
    c = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def fetchone(sql, params=()):
    with conn() as c:
        return c.execute(sql, params).fetchone()


def fetchall(sql, params=()):
    with conn() as c:
        return c.execute(sql, params).fetchall()


def execute(sql, params=()):
    with conn() as c:
        cur = c.execute(sql, params)
        try:
            return cur.fetchone()
        except psycopg.ProgrammingError:
            return None
