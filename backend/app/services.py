from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from typing import Any

import psycopg

from .db import get_users
from .repository import compute_plan_metrics, get_plan, get_user_plans, plan_day_with_checklist

BIBLE_TOTAL_CHAPTERS = 1189


def parse_day(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def pretty_day(value: date) -> str:
    return value.strftime('%d/%m/%Y')


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
