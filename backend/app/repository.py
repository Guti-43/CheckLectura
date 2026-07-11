from __future__ import annotations

from datetime import date
from typing import Any

import psycopg

from .db import (
    ensure_plan_day,
    get_plan_checkins,
    get_plan_day,
    get_plan_days,
    get_plan_members,
    get_plan_by_name,
    get_plans,
    set_plan_checkin,
    upsert_plan_day,
)


def get_user_plans(conn: psycopg.Connection[Any], user_id: int) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT p.id, p.name, p.description, p.start_day, p.chapters_per_day,
                   p.bible_total_chapters, p.sort_order, p.updated_at
            FROM plans p
            JOIN plan_members pm ON pm.plan_id = p.id
            WHERE pm.user_id = %s
            ORDER BY p.sort_order ASC, p.id ASC
            ''',
            (user_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_plan(conn: psycopg.Connection[Any], plan_id: int) -> dict[str, Any] | None:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            '''
            SELECT id, name, description, start_day, chapters_per_day, bible_total_chapters, sort_order, updated_at
            FROM plans
            WHERE id = %s
            ''',
            (plan_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def plan_day_with_checklist(conn: psycopg.Connection[Any], plan_day_id: int) -> dict[str, Any] | None:
    row = get_plan_day(conn, plan_day_id)
    if row is None:
        return None
    checklist = get_plan_checkins(conn, plan_day_id)
    data = {
        'id': row['id'],
        'plan_id': row['plan_id'],
        'day_date': row['day_date'].isoformat(),
        'day_label': row['day_date'].strftime('%d/%m/%Y'),
        'title': row['title'],
        'scripture': row['scripture'],
        'notes': row['notes'],
        'updated_at': row['updated_at'].isoformat(),
        'checklist': checklist,
        'is_read': all(item['is_read'] for item in checklist) if checklist else False,
    }
    return data


def decorate_plan_day_row(row: dict[str, Any], conn: psycopg.Connection[Any]) -> dict[str, Any]:
    checklist = get_plan_checkins(conn, row['id'])
    return {
        'id': row['id'],
        'plan_id': row['plan_id'],
        'day_date': row['day_date'].isoformat(),
        'day_label': row['day_date'].strftime('%d/%m/%Y'),
        'title': row['title'],
        'scripture': row['scripture'],
        'notes': row['notes'],
        'updated_at': row['updated_at'].isoformat(),
        'checklist': checklist,
        'is_read': all(item['is_read'] for item in checklist) if checklist else False,
    }


def plan_days_for_plan(conn: psycopg.Connection[Any], plan_id: int) -> list[dict[str, Any]]:
    rows = get_plan_days(conn, plan_id, ascending=True)
    return [decorate_plan_day_row(row, conn) for row in rows]


def compute_plan_metrics(conn: psycopg.Connection[Any], plan_id: int) -> dict[str, Any]:
    plan = get_plan(conn, plan_id)
    if plan is None:
        return {}
    members = get_plan_members(conn, plan_id)
    days = plan_days_for_plan(conn, plan_id)

    total_days = len(days)
    completed_days = sum(1 for day in days if day['is_read'])
    completion = round((completed_days / total_days) * 100, 1) if total_days else 0.0

    per_member = []
    for member in members:
        read_days = sum(
            1
            for day in days
            if any(checkin['user_id'] == member['id'] and checkin['is_read'] for checkin in day['checklist'])
        )
        missed_days = total_days - read_days
        current_streak, best_streak = _streaks(days, member['id'])
        per_member.append(
            {
                'id': member['id'],
                'name': member['name'],
                'read_days': read_days,
                'missed_days': missed_days,
                'completion': round((read_days / total_days) * 100, 1) if total_days else 0.0,
                'current_streak': current_streak,
                'best_streak': best_streak,
            }
        )

    first_reader = _first_reader_counts(days, members)

    return {
        'plan': plan,
        'members': members,
        'days': days,
        'total_days': total_days,
        'completed_days': completed_days,
        'pending_days': total_days - completed_days,
        'completion': completion,
        'per_member': per_member,
        'first_reader': first_reader,
    }


def _streaks(days: list[dict[str, Any]], user_id: int) -> tuple[int, int]:
    flags = [
        any(checkin['user_id'] == user_id and checkin['is_read'] for checkin in day['checklist'])
        for day in days
    ]
    current = 0
    for flag in reversed(flags):
        if not flag:
            break
        current += 1
    best = 0
    run = 0
    for flag in flags:
        if flag:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return current, best


def _first_reader_counts(days: list[dict[str, Any]], members: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {member['id']: 0 for member in members}
    for day in days:
        completed = [item for item in day['checklist'] if item['is_read'] and item.get('updated_at')]
        if len(completed) < 2:
            continue
        first = min(completed, key=lambda item: item['updated_at'])
        if first['user_id'] in counts:
            counts[first['user_id']] += 1
    return counts
