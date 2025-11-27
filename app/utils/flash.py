"""Petites fonctions pour gérer les messages flash stockés en session."""

from typing import List

from fastapi import Request


FLASH_KEY = "_flash_messages"


def flash(request: Request, message: str, category: str = "info") -> None:
    """Empile un message flash dans la session."""
    messages = request.session.get(FLASH_KEY, [])
    messages.append({"message": message, "category": category})
    request.session[FLASH_KEY] = messages


def pop_flashed_messages(request: Request) -> List[dict]:
    """Retourne et supprime les messages flash."""
    return request.session.pop(FLASH_KEY, [])

