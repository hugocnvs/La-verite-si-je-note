"""Script utilitaire pour créer un utilisateur (avec le hash du même algo que l'app).

Usage :
    python scripts/create_user.py --email test@gmail.com --password testtest [--username test]

Il vérifie l'existence d'un utilisateur par email ou username avant d'ajouter.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlmodel import Session, select

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.database import engine, init_db
from app.models import User
from app.security import hash_password


def create_user(username: str, email: str, password: str) -> bool:
    """Crée un utilisateur. Retourne True si créé, False si déjà existant."""
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(User).where((User.email == email) | (User.username == username))).first()
        if existing:
            print(f"⏭️ L'utilisateur existe déjà (email: {email} / username: {username}).")
            return False
        user = User(username=username.strip(), email=email.strip().lower(), hashed_password=hash_password(password))
        session.add(user)
        session.commit()
        print(f"✅ Utilisateur créé : {username} <{email}>")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer un utilisateur dans la DB")
    parser.add_argument("--email", required=True, help="Email de l'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe brut")
    parser.add_argument("--username", required=False, help="Nom d'utilisateur (par défaut: avant @ de l'email)")
    args = parser.parse_args()

    username = args.username or args.email.split("@")[0]
    email = args.email
    password = args.password

    create_user(username=username, email=email, password=password)


if __name__ == "__main__":
    main()
