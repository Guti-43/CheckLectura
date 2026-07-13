from __future__ import annotations

import os
import time
from contextlib import contextmanager
from datetime import date, timedelta
from hashlib import md5
from typing import Any, Generator

import psycopg

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://checklectura:checklectura@db:5432/checklectura',
)

DEFAULT_USERS = [
    {'name': 'Giada', 'sort_order': 1},
    {'name': 'Guti', 'sort_order': 2},
]

# Orden y número de capítulos de los 66 libros de la Reina-Valera 1960.
BIBLE_BOOKS = [
    ('Génesis', 50), ('Éxodo', 40), ('Levítico', 27), ('Números', 36), ('Deuteronomio', 34),
    ('Josué', 24), ('Jueces', 21), ('Rut', 4), ('1 Samuel', 31), ('2 Samuel', 24),
    ('1 Reyes', 22), ('2 Reyes', 25), ('1 Crónicas', 29), ('2 Crónicas', 36), ('Esdras', 10),
    ('Nehemías', 13), ('Ester', 10), ('Job', 42), ('Salmos', 150), ('Proverbios', 31),
    ('Eclesiastés', 12), ('Cantares', 8), ('Isaías', 66), ('Jeremías', 52), ('Lamentaciones', 5),
    ('Ezequiel', 48), ('Daniel', 12), ('Oseas', 14), ('Joel', 3), ('Amós', 9), ('Abdías', 1),
    ('Jonás', 4), ('Miqueas', 7), ('Nahúm', 3), ('Habacuc', 3), ('Sofonías', 3),
    ('Hageo', 2), ('Zacarías', 14), ('Malaquías', 4), ('Mateo', 28), ('Marcos', 16),
    ('Lucas', 24), ('Juan', 21), ('Hechos', 28), ('Romanos', 16), ('1 Corintios', 16),
    ('2 Corintios', 13), ('Gálatas', 6), ('Efesios', 6), ('Filipenses', 4), ('Colosenses', 4),
    ('1 Tesalonicenses', 5), ('2 Tesalonicenses', 3), ('1 Timoteo', 6), ('2 Timoteo', 4),
    ('Tito', 3), ('Filemón', 1), ('Hebreos', 13), ('Santiago', 5), ('1 Pedro', 5),
    ('2 Pedro', 3), ('1 Juan', 5), ('2 Juan', 1), ('3 Juan', 1), ('Judas', 1), ('Apocalipsis', 22),
]

DEFAULT_PLANS = [
    {
        'name': 'Plan compartido',
        'description': 'Lectura biblica diaria en pareja.',
        'start_day': '2026-06-25',
        'chapters_per_day': 3,
        'bible_total_chapters': 1189,
        'sort_order': 1,
        'members': ['Giada', 'Guti'],
    },
    {
        'name': 'Giada - Plan personal',
        'description': 'Plan privado de lectura de Giada.',
        'start_day': '2026-07-11',
        'chapters_per_day': 3,
        'bible_total_chapters': 1189,
        'sort_order': 2,
        'members': ['Giada'],
    },
    {
        'name': 'Guti - Plan personal',
        'description': 'Plan privado de lectura de Guti.',
        'start_day': '2026-07-11',
        'chapters_per_day': 3,
        'bible_total_chapters': 1189,
        'sort_order': 3,
        'members': ['Guti'],
    },
]

DEFAULT_PLAN_DAYS = {
    'Plan compartido': [
        {'day_date': '2026-06-25', 'title': 'Genesis 1-3', 'scripture': 'Genesis 1-3', 'notes': ''},
        {'day_date': '2026-06-26', 'title': 'Genesis 4-6', 'scripture': 'Genesis 4-6', 'notes': ''},
        {'day_date': '2026-06-27', 'title': 'Genesis 7-9', 'scripture': 'Genesis 7-9', 'notes': ''},
        {'day_date': '2026-06-28', 'title': 'Genesis 10-12', 'scripture': 'Genesis 10-12', 'notes': ''},
        {'day_date': '2026-06-29', 'title': 'Genesis 13-15', 'scripture': 'Genesis 13-15', 'notes': ''},
        {'day_date': '2026-06-30', 'title': 'Genesis 16-18', 'scripture': 'Genesis 16-18', 'notes': ''},
        {'day_date': '2026-07-01', 'title': 'Genesis 19-21', 'scripture': 'Genesis 19-21', 'notes': ''},
        {'day_date': '2026-07-02', 'title': 'Genesis 22-24', 'scripture': 'Genesis 22-24', 'notes': ''},
        {'day_date': '2026-07-03', 'title': 'Genesis 25-27', 'scripture': 'Genesis 25-27', 'notes': ''},
        {'day_date': '2026-07-04', 'title': 'Genesis 28-30', 'scripture': 'Genesis 28-30', 'notes': ''},
        {'day_date': '2026-07-05', 'title': 'Genesis 31-33', 'scripture': 'Genesis 31-33', 'notes': ''},
        {'day_date': '2026-07-06', 'title': 'Genesis 34-36', 'scripture': 'Genesis 34-36', 'notes': ''},
        {'day_date': '2026-07-07', 'title': 'Genesis 37-39', 'scripture': 'Genesis 37-39', 'notes': ''},
        {'day_date': '2026-07-08', 'title': 'Genesis 40-42', 'scripture': 'Genesis 40-42', 'notes': ''},
        {'day_date': '2026-07-09', 'title': 'Genesis 43-45', 'scripture': 'Genesis 43-45', 'notes': ''},
        {'day_date': '2026-07-10', 'title': 'Genesis 46-48', 'scripture': 'Genesis 46-48', 'notes': ''},
        {'day_date': '2026-07-11', 'title': 'Genesis 49-50 y Exodo 1', 'scripture': 'Genesis 49-50, Exodo 1', 'notes': ''},
        {'day_date': '2026-07-12', 'title': 'Exodo 2-4', 'scripture': 'Exodo 2-4', 'notes': ''},
        {'day_date': '2026-07-13', 'title': 'Exodo 5-7', 'scripture': 'Exodo 5-7', 'notes': ''},
    ],
    'Giada - Plan personal': [
        {'day_date': '2026-07-11', 'title': 'Genesis 49-50 y Exodo 1', 'scripture': 'Genesis 49-50, Exodo 1', 'notes': ''},
        {'day_date': '2026-07-12', 'title': 'Exodo 2-4', 'scripture': 'Exodo 2-4', 'notes': ''},
        {'day_date': '2026-07-13', 'title': 'Exodo 5-7', 'scripture': 'Exodo 5-7', 'notes': ''},
    ],
    'Guti - Plan personal': [
        {'day_date': '2026-07-11', 'title': 'Genesis 49-50 y Exodo 1', 'scripture': 'Genesis 49-50, Exodo 1', 'notes': ''},
        {'day_date': '2026-07-12', 'title': 'Exodo 2-4', 'scripture': 'Exodo 2-4', 'notes': ''},
        {'day_date': '2026-07-13', 'title': 'Exodo 5-7', 'scripture': 'Exodo 5-7', 'notes': ''},
    ],
}

DEFAULT_PLAN_CHECKINS = {
    'Plan compartido': {
        '2026-06-25': {'Giada': True, 'Guti': True},
        '2026-06-26': {'Giada': True, 'Guti': True},
        '2026-06-27': {'Giada': True, 'Guti': True},
        '2026-06-28': {'Giada': True, 'Guti': True},
        '2026-06-29': {'Giada': True, 'Guti': True},
        '2026-06-30': {'Giada': True, 'Guti': True},
        '2026-07-01': {'Giada': True, 'Guti': True},
        '2026-07-02': {'Giada': True, 'Guti': True},
        '2026-07-03': {'Giada': True, 'Guti': True},
        '2026-07-04': {'Giada': True, 'Guti': True},
        '2026-07-05': {'Giada': True, 'Guti': True},
        '2026-07-06': {'Giada': True, 'Guti': True},
        '2026-07-07': {'Giada': True, 'Guti': True},
        '2026-07-08': {'Giada': True, 'Guti': True},
        '2026-07-09': {'Giada': False, 'Guti': False},
        '2026-07-10': {'Giada': True, 'Guti': True},
        '2026-07-11': {'Giada': True, 'Guti': True},
        '2026-07-12': {'Giada': True, 'Guti': True},
        '2026-07-13': {'Giada': False, 'Guti': False},
    },
    'Giada - Plan personal': {
        '2026-07-11': {'Giada': True},
        '2026-07-12': {'Giada': True},
        '2026-07-13': {'Giada': False},
    },
    'Guti - Plan personal': {
        '2026-07-11': {'Guti': True},
        '2026-07-12': {'Guti': False},
        '2026-07-13': {'Guti': True},
    },
}


@contextmanager
def get_conn() -> Generator[psycopg.Connection[Any], None, None]:
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def wait_for_db(max_attempts: int = 20) -> None:
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                    cur.fetchone()
            return
        except Exception as exc:  # pragma: no cover - startup retry
            last_error = exc
            time.sleep(1)
    raise RuntimeError('Database is not ready') from last_error


def init_db() -> None:
    wait_for_db()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    id serial PRIMARY KEY,
                    name text NOT NULL UNIQUE,
                    password_md5 text NOT NULL,
                    sort_order integer NOT NULL DEFAULT 0
                )
                '''
            )
            cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_md5 text')
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS bible_books (
                    book_order smallint PRIMARY KEY,
                    name text NOT NULL UNIQUE,
                    chapters smallint NOT NULL CHECK (chapters > 0)
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS plans (
                    id serial PRIMARY KEY,
                    name text NOT NULL UNIQUE,
                    description text NOT NULL DEFAULT '',
                    start_day date NOT NULL,
                    chapters_per_day integer NOT NULL DEFAULT 3,
                    bible_total_chapters integer NOT NULL DEFAULT 1189,
                    start_book_order smallint NOT NULL DEFAULT 1,
                    end_book_order smallint NOT NULL DEFAULT 66,
                    is_recurring boolean NOT NULL DEFAULT false,
                    sort_order integer NOT NULL DEFAULT 0,
                    updated_at timestamptz NOT NULL DEFAULT now()
                )
                '''
            )
            cur.execute('ALTER TABLE plans ADD COLUMN IF NOT EXISTS start_book_order smallint NOT NULL DEFAULT 1')
            cur.execute('ALTER TABLE plans ADD COLUMN IF NOT EXISTS end_book_order smallint NOT NULL DEFAULT 66')
            cur.execute('ALTER TABLE plans ADD COLUMN IF NOT EXISTS is_recurring boolean NOT NULL DEFAULT false')
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS plan_members (
                    plan_id integer NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
                    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    PRIMARY KEY (plan_id, user_id)
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS plan_days (
                    id serial PRIMARY KEY,
                    plan_id integer NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
                    day_date date NOT NULL,
                    title text NOT NULL,
                    scripture text NOT NULL,
                    notes text NOT NULL DEFAULT '',
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (plan_id, day_date)
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS plan_checkins (
                    plan_day_id integer NOT NULL REFERENCES plan_days(id) ON DELETE CASCADE,
                    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    is_read boolean NOT NULL DEFAULT false,
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    PRIMARY KEY (plan_day_id, user_id)
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS plan_day_notes (
                    plan_day_id integer NOT NULL REFERENCES plan_days(id) ON DELETE CASCADE,
                    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    notes text NOT NULL DEFAULT '',
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    PRIMARY KEY (plan_day_id, user_id)
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS app_state (
                    state_key text PRIMARY KEY,
                    state_value text NOT NULL
                )
                '''
            )
            conn.commit()

        seed_bible_books(conn)
        if not _is_initial_seed_complete(conn):
            seed_users(conn)
            seed_plans(conn)
            seed_plan_members(conn)
            seed_plan_days(conn)
            seed_plan_checkins(conn)
            _mark_initial_seed_complete(conn)

        _backfill_checkin_dates_for_streaks(conn)
        _backfill_user_passwords(conn)
        _fill_empty_plan_days(conn)


def seed_bible_books(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        for book_order, (name, chapters) in enumerate(BIBLE_BOOKS, start=1):
            cur.execute(
                '''
                INSERT INTO bible_books (book_order, name, chapters)
                VALUES (%s, %s, %s)
                ON CONFLICT (book_order) DO UPDATE
                SET name = EXCLUDED.name, chapters = EXCLUDED.chapters
                ''',
                (book_order, name, chapters),
            )
    conn.commit()


def _fill_empty_plan_days(conn: psycopg.Connection[Any]) -> None:
    """Populate legacy plans that were created before automatic readings."""
    books = get_bible_books(conn)
    for plan in get_plans(conn):
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM plan_days WHERE plan_id = %s LIMIT 1', (plan['id'],))
            if cur.fetchone():
                continue
        selected_books = [
            book
            for book in books
            if plan['start_book_order'] <= book['book_order'] <= plan['end_book_order']
        ]
        if selected_books:
            generate_plan_days(
                conn,
                plan['id'],
                plan['start_day'],
                plan['chapters_per_day'],
                selected_books,
            )
    conn.commit()


def _is_initial_seed_complete(conn: psycopg.Connection[Any]) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM app_state WHERE state_key = 'initial_seed_complete'")
        return cur.fetchone() is not None


def _mark_initial_seed_complete(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO app_state (state_key, state_value) VALUES ('initial_seed_complete', 'true')"
        )
    conn.commit()


def _backfill_checkin_dates_for_streaks(conn: psycopg.Connection[Any]) -> None:
    """Give existing check-ins a sensible baseline before streak timing existed.

    This runs just once. New check-ins keep their real save time, which lets
    the streak logic distinguish a reading completed on time from one ticked
    off later.
    """
    state_key = 'checkin_dates_backfilled_for_streaks'
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM app_state WHERE state_key = %s', (state_key,))
        if cur.fetchone():
            return
        cur.execute(
            '''
            UPDATE plan_checkins AS checkin
            SET updated_at = plan_day.day_date + interval '12 hours'
            FROM plan_days AS plan_day
            WHERE plan_day.id = checkin.plan_day_id
            '''
        )
        cur.execute(
            'INSERT INTO app_state (state_key, state_value) VALUES (%s, %s)',
            (state_key, 'true'),
        )
    conn.commit()


def _password_md5(password: str) -> str:
    return md5(password.encode('utf-8')).hexdigest()


def _backfill_user_passwords(conn: psycopg.Connection[Any]) -> None:
    """Set legacy users' initial password to their exact name."""
    with conn.cursor() as cur:
        cur.execute('SELECT id, name FROM users WHERE password_md5 IS NULL OR password_md5 = %s', ('',))
        for user_id, name in cur.fetchall():
            cur.execute('UPDATE users SET password_md5 = %s WHERE id = %s', (_password_md5(name), user_id))
        cur.execute('ALTER TABLE users ALTER COLUMN password_md5 SET NOT NULL')
    conn.commit()


def seed_users(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        for user in DEFAULT_USERS:
            cur.execute(
                '''
                UPDATE users
                SET name = %s
                WHERE sort_order = %s
                ''',
                (user['name'], user['sort_order']),
            )
            if cur.rowcount == 0:
                cur.execute(
                    '''
                    INSERT INTO users (name, password_md5, sort_order)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                    ''',
                    (user['name'], _password_md5(user['name']), user['sort_order']),
                )
        conn.commit()


def get_users(conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, name, sort_order
            FROM users
            ORDER BY sort_order ASC, id ASC
            '''
        )
        return [dict(row) for row in cur.fetchall()]


def get_bible_books(conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute('SELECT book_order, name, chapters FROM bible_books ORDER BY book_order')
        return [dict(row) for row in cur.fetchall()]


def get_user_by_credentials(conn: psycopg.Connection[Any], name: str, password: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, name, sort_order
            FROM users
            WHERE name = %s AND password_md5 = %s
            ''',
            (name, _password_md5(password)),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(conn: psycopg.Connection[Any], name: str, password: str) -> dict[str, Any]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute('SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM users')
        sort_order = cur.fetchone()['next_order']
        cur.execute(
            'INSERT INTO users (name, password_md5, sort_order) VALUES (%s, %s, %s) RETURNING id, name, sort_order',
            (name, _password_md5(password), sort_order),
        )
        user = dict(cur.fetchone())
    conn.commit()
    return user


def update_user(conn: psycopg.Connection[Any], user_id: int, name: str, password: str = '') -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        if password:
            cur.execute('UPDATE users SET name = %s, password_md5 = %s WHERE id = %s RETURNING id, name, sort_order', (name, _password_md5(password), user_id))
        else:
            cur.execute('UPDATE users SET name = %s WHERE id = %s RETURNING id, name, sort_order', (name, user_id))
        row = cur.fetchone()
    conn.commit()
    return dict(row) if row else None


def delete_user(conn: psycopg.Connection[Any], user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        deleted = cur.rowcount > 0
    conn.commit()
    return deleted


def seed_plans(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        for plan in DEFAULT_PLANS:
            cur.execute(
                '''
                INSERT INTO plans (name, description, start_day, chapters_per_day, bible_total_chapters, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                SET description = EXCLUDED.description,
                    start_day = EXCLUDED.start_day,
                    chapters_per_day = EXCLUDED.chapters_per_day,
                    bible_total_chapters = EXCLUDED.bible_total_chapters,
                    sort_order = EXCLUDED.sort_order,
                    updated_at = now()
                ''',
                (
                    plan['name'],
                    plan['description'],
                    plan['start_day'],
                    plan['chapters_per_day'],
                    plan['bible_total_chapters'],
                    plan['sort_order'],
                ),
            )
        conn.commit()


def get_plans(conn: psycopg.Connection[Any]) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, name, description, start_day, chapters_per_day, bible_total_chapters,
                   start_book_order, end_book_order, is_recurring, sort_order, updated_at
            FROM plans
            ORDER BY sort_order ASC, id ASC
            '''
        )
        return [dict(row) for row in cur.fetchall()]


def get_plan_by_name(conn: psycopg.Connection[Any], name: str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, name, description, start_day, chapters_per_day, bible_total_chapters,
                   start_book_order, end_book_order, is_recurring, sort_order, updated_at
            FROM plans
            WHERE name = %s
            ''',
            (name,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def delete_plan(conn: psycopg.Connection[Any], plan_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute('DELETE FROM plans WHERE id = %s', (plan_id,))
        deleted = cur.rowcount > 0
    conn.commit()
    return deleted


def create_plan(
    conn: psycopg.Connection[Any],
    name: str,
    description: str,
    start_day: date,
    chapters_per_day: int,
    member_ids: list[int],
    start_book_order: int = 1,
    end_book_order: int = 66,
    is_recurring: bool = False,
) -> dict[str, Any]:
    books = get_bible_books(conn)
    selected_books = [book for book in books if start_book_order <= book['book_order'] <= end_book_order]
    if not selected_books:
        raise ValueError('El rango de libros no es válido')
    bible_total_chapters = sum(book['chapters'] for book in selected_books)
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute('SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM plans')
        sort_order = cur.fetchone()['next_order']
        cur.execute(
            '''
            INSERT INTO plans (
                name, description, start_day, chapters_per_day, bible_total_chapters,
                start_book_order, end_book_order, is_recurring, sort_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, description, start_day, chapters_per_day, bible_total_chapters,
                      start_book_order, end_book_order, is_recurring, sort_order, updated_at
            ''',
            (
                name, description, start_day, chapters_per_day, bible_total_chapters,
                start_book_order, end_book_order, is_recurring, sort_order,
            ),
        )
        plan = dict(cur.fetchone())
        for user_id in member_ids:
            cur.execute('INSERT INTO plan_members (plan_id, user_id) VALUES (%s, %s)', (plan['id'], user_id))
    generate_plan_days(conn, plan['id'], start_day, chapters_per_day, selected_books)
    conn.commit()
    return plan


def restart_recurring_plan(conn: psycopg.Connection[Any], plan_id: int, start_day: date) -> bool:
    plan = get_plan_by_id(conn, plan_id)
    if plan is None or not plan['is_recurring']:
        return False
    books = [
        book for book in get_bible_books(conn)
        if plan['start_book_order'] <= book['book_order'] <= plan['end_book_order']
    ]
    if not books:
        return False
    with conn.cursor() as cur:
        cur.execute('DELETE FROM plan_days WHERE plan_id = %s', (plan_id,))
        cur.execute('UPDATE plans SET start_day = %s, updated_at = now() WHERE id = %s', (start_day, plan_id))
    generate_plan_days(conn, plan_id, start_day, plan['chapters_per_day'], books)
    conn.commit()
    return True


def get_plan_by_id(conn: psycopg.Connection[Any], plan_id: int) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, start_day, chapters_per_day, start_book_order, end_book_order, is_recurring
            FROM plans WHERE id = %s
            ''',
            (plan_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def generate_plan_days(
    conn: psycopg.Connection[Any],
    plan_id: int,
    start_day: date,
    chapters_per_day: int,
    books: list[dict[str, Any]],
) -> None:
    """Create one reading entry per day for the selected biblical range."""
    chapters = [
        (book['name'], chapter)
        for book in books
        for chapter in range(1, book['chapters'] + 1)
    ]
    with conn.cursor() as cur:
        for day_index, offset in enumerate(range(0, len(chapters), chapters_per_day)):
            reading = chapters[offset:offset + chapters_per_day]
            label = _format_bible_reading(reading)
            cur.execute(
                '''
                INSERT INTO plan_days (plan_id, day_date, title, scripture, notes)
                VALUES (%s, %s, %s, %s, '')
                ON CONFLICT (plan_id, day_date) DO NOTHING
                ''',
                (plan_id, start_day + timedelta(days=day_index), label, label),
            )


def _format_bible_reading(reading: list[tuple[str, int]]) -> str:
    groups: list[tuple[str, int, int]] = []
    for book_name, chapter in reading:
        if groups and groups[-1][0] == book_name and chapter == groups[-1][2] + 1:
            groups[-1] = (book_name, groups[-1][1], chapter)
        else:
            groups.append((book_name, chapter, chapter))
    labels = [f'{name} {start}' if start == end else f'{name} {start}-{end}' for name, start, end in groups]
    return ', '.join(labels[:-1]) + (' y ' if len(labels) > 1 else '') + labels[-1]


def update_plan(
    conn: psycopg.Connection[Any],
    plan_id: int,
    name: str,
    description: str,
    start_day: date,
    chapters_per_day: int,
    member_ids: list[int],
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            UPDATE plans
            SET name = %s, description = %s, start_day = %s, chapters_per_day = %s, updated_at = now()
            WHERE id = %s
            RETURNING id, name, description, start_day, chapters_per_day, bible_total_chapters,
                      start_book_order, end_book_order, is_recurring, sort_order, updated_at
            ''',
            (name, description, start_day, chapters_per_day, plan_id),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute('DELETE FROM plan_members WHERE plan_id = %s', (plan_id,))
        for user_id in member_ids:
            cur.execute('INSERT INTO plan_members (plan_id, user_id) VALUES (%s, %s)', (plan_id, user_id))
    conn.commit()
    return dict(row)


def seed_plan_members(conn: psycopg.Connection[Any]) -> None:
    users = get_users(conn)
    user_id_by_name = {user['name']: user['id'] for user in users}
    plans = get_plans(conn)
    plan_id_by_name = {plan['name']: plan['id'] for plan in plans}

    with conn.cursor() as cur:
        for plan_name, member_names in ((plan['name'], plan['members']) for plan in DEFAULT_PLANS):
            plan_id = plan_id_by_name[plan_name]
            for member_name in member_names:
                cur.execute(
                    '''
                    INSERT INTO plan_members (plan_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    ''',
                    (plan_id, user_id_by_name[member_name]),
                )
        conn.commit()


def get_plan_members(conn: psycopg.Connection[Any], plan_id: int) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT u.id, u.name, u.sort_order
            FROM plan_members pm
            JOIN users u ON u.id = pm.user_id
            WHERE pm.plan_id = %s
            ORDER BY u.sort_order ASC, u.id ASC
            ''',
            (plan_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def seed_plan_days(conn: psycopg.Connection[Any]) -> None:
    plans = get_plans(conn)
    plan_id_by_name = {plan['name']: plan['id'] for plan in plans}
    with conn.cursor() as cur:
        for plan_name, days in DEFAULT_PLAN_DAYS.items():
            plan_id = plan_id_by_name[plan_name]
            for day in days:
                cur.execute(
                    '''
                    INSERT INTO plan_days (plan_id, day_date, title, scripture, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (plan_id, day_date) DO NOTHING
                    ''',
                    (plan_id, day['day_date'], day['title'], day['scripture'], day['notes']),
                )
        conn.commit()


def get_plan_days(conn: psycopg.Connection[Any], plan_id: int, limit: int | None = None, ascending: bool = False) -> list[dict[str, Any]]:
    order = 'ASC' if ascending else 'DESC'
    query = f'''
        SELECT id, plan_id, day_date, title, scripture, notes, updated_at
        FROM plan_days
        WHERE plan_id = %s
        ORDER BY day_date {order}
    '''
    params: tuple[Any, ...] = (plan_id,)
    if limit is not None:
        query += ' LIMIT %s'
        params = (plan_id, limit)

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_plan_day(conn: psycopg.Connection[Any], plan_day_id: int) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, plan_id, day_date, title, scripture, notes, updated_at
            FROM plan_days
            WHERE id = %s
            ''',
            (plan_day_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def ensure_plan_day(conn: psycopg.Connection[Any], plan_id: int, day: date) -> int:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            INSERT INTO plan_days (plan_id, day_date, title, scripture, notes)
            VALUES (%s, %s, '', '', '')
            ON CONFLICT (plan_id, day_date) DO UPDATE
            SET updated_at = now()
            RETURNING id
            ''',
            (plan_id, day),
        )
        row = cur.fetchone()
        conn.commit()
        return row['id']


def seed_plan_checkins(conn: psycopg.Connection[Any]) -> None:
    users = get_users(conn)
    user_id_by_name = {user['name']: user['id'] for user in users}
    plans = get_plans(conn)
    plan_id_by_name = {plan['name']: plan['id'] for plan in plans}

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        for plan_name, per_day in DEFAULT_PLAN_CHECKINS.items():
            plan_id = plan_id_by_name[plan_name]
            cur.execute('SELECT id, day_date FROM plan_days WHERE plan_id = %s', (plan_id,))
            plan_days = cur.fetchall()
            day_id_by_date = {row['day_date'].isoformat(): row['id'] for row in plan_days}
            for day_date, checkins in per_day.items():
                plan_day_id = day_id_by_date[day_date]
                for user_name, is_read in checkins.items():
                    cur.execute(
                        '''
                        INSERT INTO plan_checkins (plan_day_id, user_id, is_read, updated_at)
                        VALUES (%s, %s, %s, %s::date + interval '12 hours')
                        ON CONFLICT (plan_day_id, user_id) DO UPDATE
                        SET is_read = EXCLUDED.is_read,
                            updated_at = EXCLUDED.updated_at
                        ''',
                        (plan_day_id, user_id_by_name[user_name], is_read, day_date),
                    )
        conn.commit()


def get_plan_checkins(conn: psycopg.Connection[Any], plan_day_id: int) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT u.id AS user_id, u.name, COALESCE(c.is_read, false) AS is_read, c.updated_at
            FROM users u
            JOIN plan_members pm ON pm.user_id = u.id
            LEFT JOIN plan_checkins c
              ON c.user_id = u.id AND c.plan_day_id = %s
            WHERE pm.plan_id = (SELECT plan_id FROM plan_days WHERE id = %s)
            ORDER BY u.sort_order ASC, u.id ASC
            ''',
            (plan_day_id, plan_day_id),
        )
        return [dict(row) for row in cur.fetchall()]


def get_plan_day_notes(conn: psycopg.Connection[Any], plan_day_id: int) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT n.user_id, u.name, n.notes, n.updated_at
            FROM plan_day_notes n
            JOIN users u ON u.id = n.user_id
            WHERE n.plan_day_id = %s AND n.notes <> ''
            ORDER BY n.updated_at ASC
            ''',
            (plan_day_id,),
        )
        notes = [dict(row) for row in cur.fetchall()]
    for note in notes:
        note['updated_label'] = note['updated_at'].strftime('%d/%m/%Y %H:%M')
    return notes


def upsert_plan_day_note(
    conn: psycopg.Connection[Any], plan_day_id: int, user_id: int, notes: str
) -> dict[str, Any]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            INSERT INTO plan_day_notes (plan_day_id, user_id, notes)
            VALUES (%s, %s, %s)
            ON CONFLICT (plan_day_id, user_id) DO UPDATE
            SET notes = EXCLUDED.notes,
                updated_at = now()
            RETURNING plan_day_id, user_id, notes, updated_at
            ''',
            (plan_day_id, user_id, notes),
        )
        row = cur.fetchone()
    conn.commit()
    return dict(row)


def upsert_plan_day(conn: psycopg.Connection[Any], plan_id: int, day: date, title: str, scripture: str, notes: str) -> dict[str, Any]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            INSERT INTO plan_days (plan_id, day_date, title, scripture, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (plan_id, day_date) DO UPDATE
            SET title = EXCLUDED.title,
                scripture = EXCLUDED.scripture,
                notes = EXCLUDED.notes,
                updated_at = now()
            RETURNING id, plan_id, day_date, title, scripture, notes, updated_at
            ''',
            (plan_id, day, title, scripture, notes),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)


def set_plan_checkin(conn: psycopg.Connection[Any], plan_day_id: int, user_id: int, is_read: bool) -> dict[str, Any]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            INSERT INTO plan_checkins (plan_day_id, user_id, is_read)
            VALUES (%s, %s, %s)
            ON CONFLICT (plan_day_id, user_id) DO UPDATE
            SET is_read = EXCLUDED.is_read,
                updated_at = now()
            RETURNING plan_day_id, user_id, is_read, updated_at
            ''',
            (plan_day_id, user_id, is_read),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)
