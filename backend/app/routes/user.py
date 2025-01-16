from app.usecases.user import search_group_by_name_prefix, search_user_by_email_prefix
from app.user import User, UserGroup
from fastapi import APIRouter, Request

router = APIRouter(tags=["user"])


@router.get("/user/search", response_model=list[User])
def search_user(request: Request, prefix: str):
    """Search users"""
    current_user: User = request.state.current_user

    if not current_user.is_creating_bot_allowed():
        raise PermissionError("Search user is not allowed for the current user")

    users = search_user_by_email_prefix(prefix=prefix)
    return users


@router.get("/user/group/search", response_model=list[UserGroup])
def search_user_group(request: Request, prefix: str):
    """Search user groups"""
    current_user: User = request.state.current_user

    if not current_user.is_creating_bot_allowed():
        raise PermissionError("Search user group is not allowed for the current user")

    groups = search_group_by_name_prefix(prefix=prefix)
    return groups
