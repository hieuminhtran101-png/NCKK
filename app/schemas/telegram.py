from pydantic import BaseModel
from typing import Optional

class TelegramStatusResponse(BaseModel):
    is_telegram_linked: bool
    telegram_link: Optional[str] = None