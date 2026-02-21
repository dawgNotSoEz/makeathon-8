from datetime import datetime, timezone
from typing import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from backend.core.config import config
from backend.core.exceptions import ForbiddenError, UnauthorizedError


class AuthUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sub: str
    role: str = Field(pattern=r"^(admin|analyst|user)$")
    iss: str
    aud: str
    exp: int


security_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> AuthUser:
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret.get_secret_value(),
            algorithms=[config.jwt_algorithm],
            audience=config.jwt_audience,
            issuer=config.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc

    user = AuthUser.model_validate(payload)
    if user.exp <= int(datetime.now(timezone.utc).timestamp()):
        raise UnauthorizedError("Token expired")
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme)) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")
    return _decode_token(credentials.credentials)


def require_roles(*roles: str) -> Callable:
    async def _enforcer(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in roles:
            raise ForbiddenError("Insufficient role permissions")
        return user

    return _enforcer
