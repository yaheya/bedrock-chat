from app.repositories.user import find_group_by_name_prefix, find_users_by_email_prefix
from app.user import User, UserGroup


def search_user_by_email_prefix(prefix: str, limit: int = 10) -> list[User]:
    return find_users_by_email_prefix(prefix=prefix, limit=limit)


def search_group_by_name_prefix(prefix: str) -> list[UserGroup]:
    return find_group_by_name_prefix(prefix=prefix)
