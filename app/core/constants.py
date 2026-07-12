ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "ACTIVE": {"LEAVE", "RESIGNED"},
    "LEAVE": {"ACTIVE", "RESIGNED"},
    "RESIGNED": set(),
}

STATUS_LABEL = {
    "ACTIVE": "재직",
    "LEAVE": "휴직",
    "RESIGNED": "퇴직",
}

CHANGE_TYPE_LABEL = {
    "HIRE": "입사",
    "TRANSFER": "부서이동",
    "PROMOTION": "승진",
    "LEAVE": "휴직",
    "RETURN": "복직",
    "RESIGN": "퇴직",
}


def next_allowed_statuses(current: str) -> set[str]:
    return ALLOWED_TRANSITIONS[current]
