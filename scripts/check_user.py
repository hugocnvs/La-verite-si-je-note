"""Script pour vérifier un utilisateur par email."""
from sqlmodel import Session, select
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.database import engine
from app.models import User


def get_user_by_email(email: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email.lower().strip())).first()
        return user


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    user = get_user_by_email(args.email)
    if user:
        print('FOUND:', True)
        print('id:', user.id)
        print('username:', user.username)
        print('email:', user.email)
    else:
        print('FOUND:', False)
