from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

STATUS_BADGE = {
    "ACTIVE": {"label": "재직", "class": "badge-active"},
    "LEAVE": {"label": "휴직", "class": "badge-leave"},
    "RESIGNED": {"label": "퇴직", "class": "badge-resigned"},
}


def status_badge(value: str) -> Markup:
    meta = STATUS_BADGE[value]
    return Markup(f'<span class="badge {meta["class"]}">{meta["label"]}</span>')


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["status_badge"] = status_badge
