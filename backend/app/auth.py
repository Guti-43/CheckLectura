from __future__ import annotations

from typing import Any

import psycopg
from fastapi import Request

from .db import get_conn

SESSION_COOKIE = 'checklectura_user_id'
ADMIN_SESSION_VALUE = 'admin'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'


def get_current_user(request: Request) -> dict[str, Any] | None:
    user_id = request.cookies.get(SESSION_COOKIE)
    if not user_id:
        return None
    if user_id == ADMIN_SESSION_VALUE:
        return {'id': 0, 'name': 'Admin', 'sort_order': 0, 'is_admin': True}
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None

    with get_conn() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                '''
                SELECT id, name, sort_order
                FROM users
                WHERE id = %s
                ''',
                (user_id_int,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            user = dict(row)
            user['is_admin'] = False
            return user
