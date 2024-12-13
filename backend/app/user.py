from typing import Self

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    groups: list[str]

    def is_admin(self) -> bool:
        return "Admin" in self.groups

    def is_creating_bot_allowed(self) -> bool:
        return self.is_admin() or "CreatingBotAllowed" in self.groups

    def is_publish_allowed(self) -> bool:
        return self.is_admin() or "PublishAllowed" in self.groups

    @classmethod
    def from_decoded_token(cls, token: dict) -> Self:
        return cls(
            id=token["sub"],
            name=token["name"],
            groups=token.get("cognito:groups", []),
        )

    @classmethod
    def from_published_api_id(cls, bot_id: str) -> Self:
        api_bot_id = f"PUBLISHED_API#{bot_id}"
        return cls(
            id=api_bot_id,
            name=api_bot_id,
            # Note: Publish API is allowed to access all bot resources.
            # It should be refactored to have a more fine-grained permission.
            groups=["Admin"],
        )
