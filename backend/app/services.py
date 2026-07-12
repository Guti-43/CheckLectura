from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from typing import Any

import psycopg

from .db import get_users
from .repository import compute_plan_metrics, get_plan, get_user_plans

BIBLE_TOTAL_CHAPTERS = 1189
WEEKDAY_LABELS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']


def parse_day(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def pretty_day(value: date) -> str:
    return value.strftime('%d/%m/%Y')


def _safe_parse_day(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    try:
        return parse_day(value)
    except ValueError:
        return fallback


def _day_read_by_user(day: dict[str, Any], user_id: int) -> bool:
    return any(checkin['user_id'] == user_id and checkin['is_read'] for checkin in day['checklist'])


def _decorate_focus_day(day: dict[str, Any] | None, user_id: int) -> dict[str, Any] | None:
    if day is None:
        return None
    decorated = dict(day)
    decorated['my_is_read'] = _day_read_by_user(day, user_id)
    decorated['has_plan_day'] = True
    return decorated


def _streaks_for_user(days: list[dict[str, Any]], user_id: int) -> tuple[int, int]:
    flags = [_day_read_by_user(day, user_id) for day in days]
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


def build_plan_list_context(conn: psycopg.Connection[Any], user_id: int) -> dict[str, Any]:
    plans = get_user_plans(conn, user_id)
    user = next((item for item in get_users(conn) if item['id'] == user_id), None)
    decorated = []
    for plan in plans:
        metrics = compute_plan_metrics(conn, plan['id'])
        start_day = plan['start_day']
        estimated_total_days = ceil(plan['bible_total_chapters'] / plan['chapters_per_day'])
        estimated_finish = start_day + timedelta(days=estimated_total_days - 1)
        selected_day = metrics['days'][0] if metrics['days'] else None
        decorated.append(
            {
                'id': plan['id'],
                'name': plan['name'],
                'description': plan['description'],
                'start_day': start_day.isoformat(),
                'start_day_label': pretty_day(start_day),
                'estimated_finish': estimated_finish.isoformat(),
                'estimated_finish_label': pretty_day(estimated_finish),
                'chapters_per_day': plan['chapters_per_day'],
                'bible_total_chapters': plan['bible_total_chapters'],
                'completion': metrics['completion'],
                'completed_days': metrics['completed_days'],
                'total_days': metrics['total_days'],
                'members': metrics['members'],
                'selected_row': selected_day,
            }
        )
    return {'current_user': user, 'plans': decorated}


def build_plan_calendar_context(
    conn: psycopg.Connection[Any],
    plan_id: int,
    current_user_id: int,
    selected_day_value: str | None = None,
    week_value: str | None = None,
) -> dict[str, Any]:
    metrics = compute_plan_metrics(conn, plan_id)
    if not metrics:
        return {}

    plan = metrics['plan']
    days = metrics['days']
    day_by_date = {parse_day(day['day_date']): day for day in days}
    today = date.today()
    selected_day = _safe_parse_day(selected_day_value, today)
    week_anchor = _safe_parse_day(week_value, selected_day)
    week_start = week_anchor - timedelta(days=week_anchor.weekday())
    week_end = week_start + timedelta(days=6)

    current_user_read_days = sum(1 for day in days if _day_read_by_user(day, current_user_id))
    current_user_completion = round((current_user_read_days / metrics['total_days']) * 100, 1) if metrics['total_days'] else 0.0
    current_user_current_streak, current_user_best_streak = _streaks_for_user(days, current_user_id)

    calendar_days: list[dict[str, Any]] = []
    for offset in range(7):
        current_day = week_start + timedelta(days=offset)
        plan_day = day_by_date.get(current_day)
        user_is_read = _day_read_by_user(plan_day, current_user_id) if plan_day else False
        calendar_days.append(
            {
                'date': current_day.isoformat(),
                'label': pretty_day(current_day),
                'weekday': WEEKDAY_LABELS[current_day.weekday()],
                'is_today': current_day == today,
                'is_selected': current_day == selected_day,
                'has_plan_day': plan_day is not None,
                'plan_day': plan_day,
                'day_id': plan_day['id'] if plan_day else None,
                'title': plan_day['title'] if plan_day else '',
                'scripture': plan_day['scripture'] if plan_day else '',
                'my_is_read': user_is_read,
                'status': 'read' if user_is_read else 'pending' if plan_day else 'empty',
            }
        )

    selected_plan_day = _decorate_focus_day(day_by_date.get(selected_day), current_user_id)
    today_plan_day = _decorate_focus_day(day_by_date.get(today), current_user_id)
    spotlight_day = today_plan_day or _decorate_focus_day(next((day for day in days if parse_day(day['day_date']) >= today), None), current_user_id)

    return {
        'plan': {
            'id': plan['id'],
            'name': plan['name'],
            'description': plan['description'],
            'start_day': plan['start_day'].isoformat(),
            'start_day_label': pretty_day(plan['start_day']),
            'chapters_per_day': plan['chapters_per_day'],
            'bible_total_chapters': plan['bible_total_chapters'],
        },
        'members': metrics['members'],
        'days': days,
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'prev_week': (week_start - timedelta(days=7)).isoformat(),
        'next_week': (week_start + timedelta(days=7)).isoformat(),
        'week_label': f'{pretty_day(week_start)} - {pretty_day(week_end)}',
        'calendar_days': calendar_days,
        'selected_day': selected_plan_day,
        'selected_day_label': pretty_day(selected_day),
        'selected_day_is_today': selected_day == today,
        'today_day': spotlight_day,
        'today_label': pretty_day(today),
        'current_user_read_days': current_user_read_days,
        'current_user_pending_days': metrics['total_days'] - current_user_read_days,
        'current_user_completion': current_user_completion,
        'current_user_current_streak': current_user_current_streak,
        'current_user_best_streak': current_user_best_streak,
        'completion': metrics['completion'],
        'total_days': metrics['total_days'],
        'completed_days': metrics['completed_days'],
        'pending_days': metrics['pending_days'],
    }


def build_plan_detail_context(conn: psycopg.Connection[Any], plan_id: int) -> dict[str, Any]:
    metrics = compute_plan_metrics(conn, plan_id)
    if not metrics:
        return {}
    plan = metrics['plan']
    estimated_total_days = ceil(plan['bible_total_chapters'] / plan['chapters_per_day'])
    estimated_finish = plan['start_day'] + timedelta(days=estimated_total_days - 1)
    latest_day = metrics['days'][0] if metrics['days'] else None
    return {
        'plan': {
            'id': plan['id'],
            'name': plan['name'],
            'description': plan['description'],
            'start_day': plan['start_day'].isoformat(),
            'start_day_label': pretty_day(plan['start_day']),
            'chapters_per_day': plan['chapters_per_day'],
            'bible_total_chapters': plan['bible_total_chapters'],
            'estimated_finish': estimated_finish.isoformat(),
            'estimated_finish_label': pretty_day(estimated_finish),
            'estimated_total_days': estimated_total_days,
        },
        'members': metrics['members'],
        'days': metrics['days'],
        'total_days': metrics['total_days'],
        'completed_days': metrics['completed_days'],
        'pending_days': metrics['pending_days'],
        'completion': metrics['completion'],
        'per_member': metrics['per_member'],
        'first_reader': metrics['first_reader'],
        'latest_day': latest_day,
    }




