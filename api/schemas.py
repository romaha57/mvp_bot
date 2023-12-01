from pydantic import BaseModel


class StrResponse(BaseModel):
    """Модель ответа для строкового ответа"""

    answer: str
