from __future__ import annotations

"""Routes pour l'inscription et la connexion."""

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from ..database import get_session
from ..dependencies import get_current_user
from ..models import User
from ..security import hash_password, verify_password
from ..utils.flash import flash
from ..web import template_context, templates


router = APIRouter(tags=["auth"])


@router.get("/register")
def register_form(
    request: Request,
    current_user: User | None = Depends(get_current_user),
) -> Response:
    """Affiche le formulaire d'inscription."""
    if current_user:
        return RedirectResponse(url="/films", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "auth/register.html", template_context(request, current_user=None)
    )


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """Crée un nouvel utilisateur."""
    if password != confirm_password:
        flash(request, "Les mots de passe ne correspondent pas.", "error")
        return RedirectResponse(
            url="/register", status_code=status.HTTP_303_SEE_OTHER
        )

    if len(password) < 6:
        flash(request, "Le mot de passe doit contenir au moins 6 caractères.", "error")
        return RedirectResponse(
            url="/register", status_code=status.HTTP_303_SEE_OTHER
        )

    existing = session.exec(
        select(User).where((User.email == email) | (User.username == username))
    ).first()
    if existing:
        flash(request, "Ce nom d'utilisateur ou email est déjà pris.", "error")
        return RedirectResponse("/register", status_code=status.HTTP_303_SEE_OTHER)

    user = User(username=username.strip(), email=email.strip().lower(), hashed_password=hash_password(password))
    session.add(user)
    session.commit()

    flash(request, "Bienvenue ! Vous pouvez maintenant vous connecter.", "success")
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(
    request: Request,
    current_user: User | None = Depends(get_current_user),
) -> Response:
    """Affiche la page de connexion."""
    if current_user:
        return RedirectResponse(url="/films", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("auth/login.html", template_context(request, current_user=None))


@router.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """Connexion utilisateur."""
    user = session.exec(select(User).where(User.email == email.lower().strip())).first()
    if not user or not verify_password(password, user.hashed_password):
        flash(request, "Identifiants invalides.", "error")
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    request.session["user_id"] = user.id
    flash(request, f"Heureux de vous revoir, {user.username} !", "success")
    return RedirectResponse("/films", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout_user(request: Request) -> RedirectResponse:
    """Déconnecte l'utilisateur."""
    request.session.pop("user_id", None)
    flash(request, "À bientôt !", "info")
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

