"""登录相关。

练手项目不引入 JWT 库与密码学：签发的 token 就是 `dev-<username>`，
`/auth/me` 靠它反查用户。真实项目请换 OAuth2PasswordBearer + argon2，
接口形状不变，前端不用改。
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from app import models
from app.db import get_session
from app.schemas import LoginIn, LoginOut

router = APIRouter(prefix="/auth", tags=["认证"])

ALLOWED_PASSWORDS = {"admin": "admin123", "developer": "dev123", "viewer": "view123"}


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, session: Session = Depends(get_session)) -> LoginOut:
    # 登录页的字段叫「邮箱地址」，所以 username / email 都接受
    identifier = payload.username.strip()
    user = session.exec(
        select(models.User).where(
            (models.User.username == identifier) | (models.User.email == identifier)
        )
    ).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    expected = ALLOWED_PASSWORDS.get(user.username)
    if expected is None or payload.password != expected:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return LoginOut(
        token=f"dev-{user.username}",
        user={
            "id": user.id,
            "username": user.username,
            "displayName": user.display_name,
            "email": user.email,
            "role": user.role,
        },
    )


@router.get("/me")
def me(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization: Bearer <token>")
    username = authorization.removeprefix("Bearer ").removeprefix("dev-")
    user = session.exec(select(models.User).where(models.User.username == username)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="token 无效")
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "email": user.email,
        "role": user.role,
    }
