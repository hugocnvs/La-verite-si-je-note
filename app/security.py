"""Outils liés à la sécurité (mots de passe)."""

from passlib.context import CryptContext

# pbkdf2_sha256 ne dépend d'aucune extension système et évite les erreurs liées à bcrypt.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Retourne un hash sécurisé pour le mot de passe."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash."""
    return pwd_context.verify(password, hashed_password)

