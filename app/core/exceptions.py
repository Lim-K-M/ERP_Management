class EmployeeValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


class EmployeeNotFoundError(Exception):
    def __init__(self, emp_id: int):
        self.emp_id = emp_id
        super().__init__(f"employee {emp_id} not found")


class InvalidTransitionError(Exception):
    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(f"{current} -> {target} 전이는 허용되지 않습니다.")
