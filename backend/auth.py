"""Access-token verification. Replace `verify_access_token` to use your own identity provider."""

import jwt
from fastapi import HTTPException, Request

from .models import User

AUTH_SECRET_ENV = "AUTH_SECRET"  # where `backend.app` reads the secret from


def verify_access_token(token: str, secret: str | None) -> User:
    """Turn an Access token into the User it was issued to, or raise `jwt.PyJWTError`.

    This is the one place that decides whether a token is valid: replace it to use your own
    identity provider. The rest of the backend only ever sees the User it returns.
    """
    if not secret:
        # No default: an unconfigured deployment must not accept tokens signed with a
        # well-known secret.
        raise RuntimeError(f"{AUTH_SECRET_ENV} is not set")
    claims = jwt.decode(
        token, secret, algorithms=["HS256"], options={"require": ["exp", "sub", "name"]}
    )
    return User(id=claims["sub"], name=claims["name"])


def authorised_user(request: Request) -> User:
    """The User behind the request's bearer token, or a 401."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Sign in first: send an Access token as a bearer token.")
    try:
        return verify_access_token(token, request.app.state.auth_secret)
    except jwt.PyJWTError:
        raise HTTPException(401, "The Access token is not valid.") from None
