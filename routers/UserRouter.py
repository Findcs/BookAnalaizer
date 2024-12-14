from fastapi import APIRouter
from fastapi import Depends

from configs.Database import User
from schemas.UserSchemas import UserRead, UserCreate, UserUpdate
from services.UserService import current_active_user, auth_backend, fastapi_users

UserRouter = APIRouter(
    prefix="/v1/user"
)

UserRouter.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
UserRouter.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
UserRouter.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
UserRouter.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
UserRouter.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@UserRouter.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
