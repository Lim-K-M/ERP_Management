---
name: jinja2-ssr-frontend
description: "Jinja2 서버사이드 렌더링 화면 레이어 — 템플릿 상속(base/블록), PRG(POST→303 리다이렉트) 패턴, 상태 배지 커스텀 필터, autoescape/CSRF 트레이드오프. Jinja2 화면(페이지) 추가·폼 제출 처리 시 적용."
---
# Jinja2 SSR 프론트 레이어

이 프로젝트(`ERP_Management`)의 Jinja2 서버사이드 렌더링 화면 레이어 표준.

## 경계 (담당 / 위임)
- **담당**: `app/templates/`의 화면 구성(템플릿 상속·블록·include), 폼 제출 후 PRG 리다이렉트, 상태 배지 커스텀 필터, `app/static/`(CSS/JS).
- **위임**: 라우터의 실제 요청 처리·Service 호출·Pydantic 검증 → [`fastapi-service-architecture`](../fastapi-service-architecture/SKILL.md). 이 스킬은 라우터가 반환하는 컨텍스트를 템플릿으로 렌더링하는 부분만 담당한다.

## 0. 템플릿 상속 구조
```text
app/templates/
├── base.html                # 공용 골격: {% block title %}, {% block content %}, nav include
├── partials/
│   └── _nav.html             # 상단 네비게이션 (base.html에서 include)
└── employees/
    ├── list.html              # {% extends "base.html" %}
    ├── _form.html              # 등록/수정 공용 폼 파편 ({% include %}로 재사용)
    ├── register.html
    └── detail.html
```
- 상태 배지는 별도 partial이 아니라 §2의 `status_badge` Jinja 필터로 렌더링한다.
- `base.html`에 `{% block title %}`, `{% block content %}`를 정의하고, 하위 템플릿은 `{% extends "base.html" %}` + `{% block content %}...{% endblock %}`로 채운다.
- 등록/수정처럼 구조가 같은 화면은 `_form.html`을 `{% include "employees/_form.html" %}`로 재사용하고, 등록/수정 각각 다른 컨텍스트(초기값·에러)만 전달한다.

## 1. PRG 패턴 (POST → 303 → GET)
폼 제출 성공 시 같은 URL을 새로고침해도 중복 제출되지 않도록 POST 후 303으로 리다이렉트한다.

```python
@router.post("/employees/new")
async def create_employee(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    try:
        employee = await employee_service.create(session, EmployeeCreate(**form))
    except ValidationFailed as e:
        return templates.TemplateResponse(
            request,
            "employees/register.html",
            {"errors": e.errors, "form": form},
            status_code=422,
        )
    return RedirectResponse(f"/employees/{employee.emp_id}", status_code=303)
```
- `Jinja2Templates.TemplateResponse`는 최신 시그니처가 `(request, name, context, ...)` 순서다(`request`를 context 딕셔너리에 넣지 않는다). 이 순서를 지키지 않으면 실제로 런타임 에러가 난다 — 이 프로젝트에서 실제로 겪은 버그.
- 실패 시에는 리다이렉트하지 않고 **같은 폼 템플릿을 에러와 함께 다시 렌더링**한다(입력값 유지, 스펙 F-02 "실패 시 에러 메시지와 함께 폼 재표시").
- 303(See Other)을 쓴다 — 302는 구현체에 따라 POST를 그대로 재전송할 수 있어 부적합하다.

## 2. 상태 배지 커스텀 필터
스펙 §2의 3개 고정 상태값만 표시하므로 커스텀 Jinja2 필터로 배지를 렌더링한다.

```python
from markupsafe import Markup

STATUS_BADGE = {
    "ACTIVE": {"label": "재직", "class": "badge-active"},
    "LEAVE": {"label": "휴직", "class": "badge-leave"},
    "RESIGNED": {"label": "퇴직", "class": "badge-resigned"},
}


def status_badge(value: str) -> Markup:
    meta = STATUS_BADGE[value]
    return Markup(f'<span class="badge {meta["class"]}">{meta["label"]}</span>')


templates.env.filters["status_badge"] = status_badge
```
```jinja
{{ employee.emp_status | status_badge }}
```
- 배지 HTML은 `Markup`으로 감싸 autoescape를 의도적으로 우회한다 — 입력값이 고정된 3종 상태값(`ACTIVE`/`LEAVE`/`RESIGNED`)뿐이라 XSS 위험이 없다. **사용자 입력을 이 필터에 그대로 통과시키지 않는다.**
- 목록/상세 화면 모두 이 필터 하나로 배지를 렌더링해 F-04 "상태 변경 시 배지 즉시 반영"을 자연스럽게 만족시킨다(PRG로 재조회된 최신 상태를 그대로 필터에 통과).

## 3. autoescape / CSRF 트레이드오프
- Jinja2 `autoescape`는 **기본 활성화 상태를 유지**한다 — 이름·이메일·비고처럼 사용자 입력이 그대로 출력되는 필드를 보호한다. `| safe`나 `Markup`은 §2의 배지처럼 값이 고정된 경우에만 예외적으로 쓴다.
- CSRF 토큰은 **도입하지 않는다** — 스펙 §7 "인증 없음, 배포하지 않는 로컬 데모"이므로 세션/쿠키 기반 위조가 성립할 인증 컨텍스트가 없다. 이는 **알려진 트레이드오프**이며, 이후 인증을 도입하면 재검토가 필요하다.
