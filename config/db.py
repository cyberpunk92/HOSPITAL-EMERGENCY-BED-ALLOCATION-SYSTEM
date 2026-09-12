"""Oracle database layer: connection pool + query helpers.

All callers use the helper functions (fetch_all / fetch_one / execute /
transaction). Rows are returned as dicts keyed by lower-cased column name.
"""

import contextlib

import oracledb

from config.settings import settings

_pool = None


def init_pool():
    """Create the global connection pool. Call once at app startup."""
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dsn=settings.DB_DSN,
            min=settings.DB_POOL_MIN,
            max=settings.DB_POOL_MAX,
            increment=settings.DB_POOL_INCREMENT,
        )
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextlib.contextmanager
def get_connection():
    """Acquire a pooled connection; released back to the pool on exit."""
    if _pool is None:
        init_pool()
    conn = _pool.acquire()
    try:
        yield conn
    finally:
        _pool.release(conn)


def _dict_cursor(conn):
    cur = conn.cursor()

    def rowfactory(*args):
        cols = [d[0].lower() for d in cur.description]
        return dict(zip(cols, args))

    cur.rowfactory = rowfactory
    return cur, rowfactory


def fetch_all(sql, params=None):
    """Return a list of dict rows."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        cols = [d[0].lower() for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        return rows


def fetch_one(sql, params=None):
    """Return a single dict row, or None."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        cols = [d[0].lower() for d in cur.description]
        row = cur.fetchone()
        cur.close()
        return dict(zip(cols, row)) if row else None


def fetch_scalar(sql, params=None):
    """Return the first column of the first row, or None."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None


def execute(sql, params=None, commit=True):
    """Run a DML statement. Returns affected row count."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params or {})
            count = cur.rowcount
            if commit:
                conn.commit()
            return count
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def execute_returning_id(sql, params=None, id_var="new_id"):
    """Run an INSERT ... RETURNING <col> INTO :new_id and return the value."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            out = cur.var(oracledb.NUMBER)
            merged = dict(params or {})
            merged[id_var] = out
            cur.execute(sql, merged)
            conn.commit()
            val = out.getvalue()
            if isinstance(val, list):
                val = val[0]
            return int(val) if val is not None else None
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


@contextlib.contextmanager
def transaction():
    """Context manager yielding a cursor inside a single transaction.

    Commits on success, rolls back on exception. Use for multi-statement
    workflows (e.g. admission + bed assignment).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
