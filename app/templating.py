from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.core.constants import CHANGE_TYPE_LABEL

STATUS_BADGE = {
    "ACTIVE": {"label": "재직", "class": "badge-active"},
    "LEAVE": {"label": "휴직", "class": "badge-leave"},
    "RESIGNED": {"label": "퇴직", "class": "badge-resigned"},
}


def status_badge(value: str) -> Markup:
    meta = STATUS_BADGE[value]
    return Markup(f'<span class="badge {meta["class"]}">{meta["label"]}</span>')


def change_type_label(value: str) -> str:
    return CHANGE_TYPE_LABEL.get(value, value)


def is_logged_in(request) -> bool:
    return bool(request.session.get("user"))


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["status_badge"] = status_badge
templates.env.filters["change_type_label"] = change_type_label
templates.env.globals["is_logged_in"] = is_logged_in
