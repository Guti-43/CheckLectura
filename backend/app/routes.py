from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import ADMIN_PASSWORD, ADMIN_SESSION_VALUE, ADMIN_USERNAME, SESSION_COOKIE, get_current_user
from .db import create_user, delete_user, get_conn, get_user_by_credentials, get_users, update_user
from .i18n import translate
from .repository import (
    delete_plan,
    create_plan,
    get_plan,
    get_plan_day,
    set_plan_checkin,
    upsert_plan_day,
    upsert_plan_day_note,
    update_plan,
)
from .services import (
    build_plan_calendar_context,
    build_plan_detail_context,
    build_plan_list_context,
    parse_day,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / 'templates'))
templates.env.filters['t'] = translate


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
def login(name: str = Form(''), password: str = Form('')) -> RedirectResponse:
    clean_name = name.strip()
    if clean_name == ADMIN_USERNAME:
        if password != ADMIN_PASSWORD:
            return RedirectResponse(url='/login?error=admin', status_code=303)
        response = RedirectResponse(url='/admin', status_code=303)
        response.set_cookie(SESSION_COOKIE, ADMIN_SESSION_VALUE, httponly=True, samesite='lax')
        return response
    with get_conn() as conn:
        user = get_user_by_credentials(conn, clean_name, password)
    if user is None:
        return RedirectResponse(url='/login?error=credentials', status_code=303)
    response = RedirectResponse(url='/plans', status_code=303)
    response.set_cookie(SESSION_COOKIE, str(user['id']), httponly=True, samesite='lax')
    return response


@router.get('/signup', response_class=HTMLResponse)
def signup_form(request: Request):
    if get_current_user(request):
        return _plans_redirect()
    return templates.TemplateResponse('signup.html', {'request': request, 'page_title': 'Crear cuenta - CheckLectura'})


@router.post('/signup')
def signup(name: str = Form(''), password: str = Form('')) -> RedirectResponse:
    clean_name = name.strip()
    if not clean_name or not password or clean_name.lower() == ADMIN_USERNAME:
        return RedirectResponse(url='/signup?error=invalid', status_code=303)

    with get_conn() as conn:
        # Usernames are case-sensitive at login, but reserve case variants to
        # avoid creating confusingly similar accounts.
        if clean_name.lower() in {user['name'].lower() for user in get_users(conn)}:
            return RedirectResponse(url='/signup?error=taken', status_code=303)
        user = create_user(conn, clean_name, password)

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
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    if current_user.get('is_admin'):
        return RedirectResponse(url='/admin', status_code=303)
    return _plans_redirect()


@router.get('/plans')
def plans_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    if current_user.get('is_admin'):
        return RedirectResponse(url='/admin', status_code=303)
    with get_conn() as conn:
        context = build_plan_list_context(conn, current_user['id'])
    return templates.TemplateResponse(
        'plans.html',
        {'request': request, 'users': get_users_for_plans(), 'today_iso': date.today().isoformat(), **context},
    )


def get_users_for_plans():
    with get_conn() as conn:
        return get_users(conn)


def _admin_only(request: Request) -> RedirectResponse | None:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    if not current_user.get('is_admin'):
        return _plans_redirect()
    return None


@router.get('/admin')
def admin_page(request: Request):
    redirect = _admin_only(request)
    if redirect:
        return redirect
    with get_conn() as conn:
        users = get_users(conn)
    return templates.TemplateResponse('admin.html', {'request': request, 'current_user': get_current_user(request), 'users': users})


@router.post('/admin/users/create')
def admin_create_user(request: Request, name: str = Form(''), password: str = Form('')) -> RedirectResponse:
    redirect = _admin_only(request)
    if redirect:
        return redirect
    clean_name = name.strip()
    if clean_name and password and clean_name.lower() != ADMIN_USERNAME:
        with get_conn() as conn:
            if clean_name.lower() not in {user['name'].lower() for user in get_users(conn)}:
                create_user(conn, clean_name, password)
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/admin/users/{user_id}/update')
def admin_update_user(request: Request, user_id: int, name: str = Form(''), password: str = Form('')) -> RedirectResponse:
    redirect = _admin_only(request)
    if redirect:
        return redirect
    clean_name = name.strip()
    if clean_name and clean_name.lower() != ADMIN_USERNAME:
        with get_conn() as conn:
            names = {user['name'].lower() for user in get_users(conn) if user['id'] != user_id}
            if clean_name.lower() not in names:
                update_user(conn, user_id, clean_name, password)
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/admin/users/{user_id}/delete')
def admin_delete_user(request: Request, user_id: int) -> RedirectResponse:
    redirect = _admin_only(request)
    if redirect:
        return redirect
    with get_conn() as conn:
        delete_user(conn, user_id)
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/plans/create')
def create_plan_page(
    request: Request,
    name: str = Form(''),
    description: str = Form(''),
    start_day: str = Form(''),
    chapters_per_day: int = Form(3),
    member_ids: list[int] = Form([]),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    selected_members = set(member_ids) | {current_user['id']}
    with get_conn() as conn:
        valid_user_ids = {user['id'] for user in get_users(conn)}
        create_plan(
            conn,
            name.strip() or 'Plan sin nombre',
            description.strip(),
            parse_day(start_day) if start_day else date.today(),
            max(chapters_per_day, 1),
            sorted(selected_members & valid_user_ids),
        )
    return _plans_redirect()


@router.post('/plans/{plan_id}/update')
def update_plan_page(
    request: Request,
    plan_id: int,
    name: str = Form(''),
    description: str = Form(''),
    start_day: str = Form(''),
    chapters_per_day: int = Form(3),
    member_ids: list[int] = Form([]),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        user_plans = build_plan_list_context(conn, current_user['id'])['plans']
        if plan_id not in {plan['id'] for plan in user_plans}:
            return _plans_redirect()
        valid_user_ids = {user['id'] for user in get_users(conn)}
        update_plan(
            conn,
            plan_id,
            name.strip() or 'Plan sin nombre',
            description.strip(),
            parse_day(start_day) if start_day else date.today(),
            max(chapters_per_day, 1),
            sorted((set(member_ids) & valid_user_ids) | {current_user['id']}),
        )
    return _plans_redirect()


@router.post('/plans/{plan_id}/delete')
def delete_plan_page(request: Request, plan_id: int) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        user_plans = build_plan_list_context(conn, current_user['id'])['plans']
        if plan_id not in {plan['id'] for plan in user_plans}:
            return _plans_redirect()
        delete_plan(conn, plan_id)
    return _plans_redirect()


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


@router.post('/plans/{plan_id}/days/{day_id}/notes')
def save_my_plan_day_notes(
    request: Request,
    plan_id: int,
    day_id: int,
    notes: str = Form(''),
    week: str = Form(''),
    day: str = Form(''),
) -> RedirectResponse:
    current_user = get_current_user(request)
    if current_user is None:
        return _login_redirect()
    with get_conn() as conn:
        current_day = get_plan_day(conn, day_id)
        if current_day is None or current_day['plan_id'] != plan_id:
            return _plans_redirect()
        upsert_plan_day_note(conn, day_id, current_user['id'], notes.strip())
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
