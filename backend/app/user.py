from typing import Self

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str
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
            email=token["email"],
            groups=token.get("cognito:groups", []),
        )

    @classmethod
    def from_published_api_id(cls, bot_id: str) -> Self:
        api_bot_id = f"PUBLISHED_API#{bot_id}"
        return cls(
            id=api_bot_id,
            name=api_bot_id,
            email=api_bot_id,  # dummy email
            # Note: Publish API is allowed to access all bot resources.
            # It should be refactored to have a more fine-grained permission.
            groups=["Admin"],
        )

    @classmethod
    def from_cognito_idp_response(cls, user: dict) -> Self:
        return cls(
            id=user["Username"],
            name=next(
                attr["Value"] for attr in user["Attributes"] if attr["Name"] == "name"
            ),
            email=next(
                attr["Value"] for attr in user["Attributes"] if attr["Name"] == "email"
            ),
            groups=[],
        )


class UserGroup(BaseModel):
    name: str
    description: str

    @classmethod
    def from_cognito_idp_response(cls, group: dict) -> Self:
        return cls(
            name=group["GroupName"],
            description=group.get("Description", ""),
        )
