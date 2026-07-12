from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import SESSION_COOKIE, get_current_user
from .db import get_conn, get_users
from .repository import get_plan, get_plan_day, set_plan_checkin, upsert_plan_day
from .services import (
    build_plan_calendar_context,
    build_plan_detail_context,
    build_plan_list_context,
    parse_day,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / 'templates'))


def _login_redirect() -> RedirectResponse:
    return RedirectResponse(url='/login', status_code=303)


def _plans_redirect() -> RedirectResponse:
    return RedirectResponse(url='/plans', status_code=303)


@router.get('/login', response_class=HTMLResponse)
def login_form(request: Request):
    if get_current_user(request):
        return _plans_redirect()
    return templates.TemplateResponse('login.html', {'request': request, 'page_title': 'Login - CheckLectura'})


@router.post('/login')
def login(name: str = Form('')) -> RedirectResponse:
    clean_name = name.strip()
    with get_conn() as conn:
        users = get_users(conn)
    user = next((item for item in users if item['name'].lower() == clean_name.lower()), None)
    if user is None:
        return RedirectResponse(url='/login?error=1', status_code=303)
    response = RedirectResponse(url='/plans', status_code=303)
    response.set_cookie(SESSION_COOKIE, str(user['id']), httponly=True, samesite='lax')
    return response


@router.post('/logout')
def logout() -> RedirectResponse:
    response = RedirectResponse(url='/login', status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get('/')
def root(request: Request):
    if get_current_user(request) is None:
        return _login_redirect()
    return _plans_redirect()


@router.get('/plans')
def plans_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        context = build_plan_list_context(conn, current_user['id'])
    return templates.TemplateResponse('plans.html', {'request': request, **context})


@router.get('/plans/{plan_id}')
def plan_detail(request: Request, plan_id: int, day: str = '', week: str = ''):
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        user_plans = build_plan_list_context(conn, current_user['id'])['plans']
        if plan_id not in {plan['id'] for plan in user_plans}:
            return _plans_redirect()
        current_plan = get_plan(conn, plan_id)
        if current_plan is None:
            return _plans_redirect()
        context = build_plan_calendar_context(conn, plan_id, current_user['id'], day or None, week or None)
    return templates.TemplateResponse(
        'plan_detail.html',
        {
            'request': request,
            'current_user': current_user,
            'plans': user_plans,
            **context,
        },
    )


@router.get('/plans/{plan_id}/info')
def plan_info(request: Request, plan_id: int):
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        user_plans = build_plan_list_context(conn, current_user['id'])['plans']
        if plan_id not in {plan['id'] for plan in user_plans}:
            return _plans_redirect()
        current_plan = get_plan(conn, plan_id)
        if current_plan is None:
            return _plans_redirect()
        context = build_plan_detail_context(conn, plan_id)
    return templates.TemplateResponse(
        'plan_info.html',
        {
            'request': request,
            'current_user': current_user,
            'plans': user_plans,
            **context,
        },
    )


@router.post('/plans/{plan_id}/days/{day_id}/save')
def save_plan_day(
    request: Request,
    plan_id: int,
    day_id: int,
    day_date: str = Form(''),
    title: str = Form(''),
    scripture: str = Form(''),
    notes: str = Form(''),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        current_day = get_plan_day(conn, day_id)
        if current_day is None:
            return _plans_redirect()
        target_day = parse_day(day_date) if day_date else current_day['day_date']
        upsert_plan_day(conn, plan_id, target_day, title.strip(), scripture.strip(), notes.strip())
    return RedirectResponse(url=f'/plans/{plan_id}/info', status_code=303)


@router.post('/plans/{plan_id}/days/{day_id}/mine')
def toggle_my_plan_checkin(
    request: Request,
    plan_id: int,
    day_id: int,
    is_read: bool = Form(False),
    week: str = Form(''),
    day: str = Form(''),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        current_day = get_plan_day(conn, day_id)
        if current_day is None:
            return _plans_redirect()
        set_plan_checkin(conn, day_id, current_user['id'], is_read)
    redirect_url = f'/plans/{plan_id}?day={day or current_day["day_date"].isoformat()}'
    if week:
        redirect_url += f'&week={week}'
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post('/plans/{plan_id}/days/{day_id}/checkins/{user_id}')
def toggle_plan_checkin(
    request: Request,
    plan_id: int,
    day_id: int,
    user_id: int,
    is_read: bool = Form(False),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        set_plan_checkin(conn, day_id, user_id, is_read)
    return RedirectResponse(url=f'/plans/{plan_id}/info', status_code=303)
