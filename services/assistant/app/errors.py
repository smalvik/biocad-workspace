class AssistantError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def unavailable():
    return AssistantError(
        503, "AI_UNAVAILABLE", "AI сейчас недоступен. Выберите место на плане и забронируйте через форму."
    )
