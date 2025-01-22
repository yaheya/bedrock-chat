from typing import Any, Dict, List, Self, Type, get_args

from app.config import DEFAULT_GENERATION_CONFIG
from app.config import GenerationParams as GenerationParamsDict
from app.repositories.models.common import DynamicBaseModel, Float
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.repositories.models.custom_bot_kb import BedrockKnowledgeBaseModel
from app.routes.schemas.bot import (
    ActiveModelsOutput,
    Agent,
    BedrockGuardrailsOutput,
    BedrockKnowledgeBaseOutput,
    BotInput,
    BotMetaOutput,
    BotOutput,
    BotSummaryOutput,
    ConversationQuickStarter,
    GenerationParams,
    Knowledge,
    type_shared_scope,
    type_sync_status,
)
from app.routes.schemas.conversation import type_model_name
from app.user import User
from app.utils import get_current_time, get_user_cognito_groups
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    create_model,
    field_validator,
    model_validator,
)


def _create_model_activate_model(model_names: List[str]) -> Type[DynamicBaseModel]:
    fields: Dict[str, Any] = {
        name.replace("-", "_").replace(".", "_"): (bool, True) for name in model_names
    }
    return create_model("ActiveModelsModel", __base__=DynamicBaseModel, **fields)


ActiveModelsModel: Type[BaseModel] = _create_model_activate_model(
    list(get_args(type_model_name))
)


default_active_models = ActiveModelsModel.model_validate(
    {field_name: True for field_name in ActiveModelsModel.model_fields.keys()}
)


class KnowledgeModel(BaseModel):
    source_urls: list[str]
    sitemap_urls: list[str]
    filenames: list[str]
    s3_urls: list[str]

    def __str_in_claude_format__(self) -> str:
        """Description of the knowledge in Claude format."""
        _source_urls = "<source_urls>"
        for url in self.source_urls:
            _source_urls += f"<url>{url}</url>"
        _source_urls += "</source_urls>"
        _sitemap_urls = "<sitemap_urls>"
        for url in self.sitemap_urls:
            _sitemap_urls += f"<url>{url}</url>"
        _sitemap_urls += "</sitemap_urls>"
        _filenames = "<filenames>"
        for filename in self.filenames:
            _filenames += f"<filename>{filename}</filename>"
        _filenames += "</filenames>"
        _s3_urls = "<s3_urls>"
        for url in self.s3_urls:
            _s3_urls += f"<url>{url}</url>"
        _s3_urls += "</s3_urls>"
        return f"{_source_urls}{_sitemap_urls}{_filenames}{_s3_urls}"


class GenerationParamsModel(BaseModel):
    max_tokens: int
    top_k: int
    top_p: Float
    temperature: Float
    stop_sequences: list[str]


class AgentToolModel(BaseModel):
    name: str
    description: str


class AgentModel(BaseModel):
    tools: list[AgentToolModel]


class ConversationQuickStarterModel(BaseModel):
    title: str
    example: str


class BotModel(BaseModel):
    id: str
    owner_user_id: str
    title: str
    description: str
    instruction: str
    create_time: Float

    # SK
    last_used_time: Float
    # GSI-2 PK (SharedScopeIndex)
    shared_scope: type_shared_scope = Field(
        ..., description="`partial` or `all` or None. None means the bot is not shared."
    )
    # GSI-2 SK (SharedScopeIndex)
    shared_status: str = Field(
        ...,
        description="`unshared`, `shared`, or `pinned@xxx` (xxx is a 3-digit integer)",
    )
    allowed_cognito_groups: list[str]
    allowed_cognito_users: list[str]
    # LSI-1 SK (StarredIndex)
    is_starred: bool

    # # This can be used as the bot is public or not. Also used for GSI PK
    # public_bot_id: str | None
    # is_starred: bool

    generation_params: GenerationParamsModel
    agent: AgentModel
    knowledge: KnowledgeModel
    sync_status: type_sync_status
    sync_status_reason: str
    sync_last_exec_id: str
    published_api_stack_name: str | None
    published_api_datetime: int | None
    published_api_codebuild_id: str | None
    display_retrieved_chunks: bool
    conversation_quick_starters: list[ConversationQuickStarterModel]
    bedrock_knowledge_base: BedrockKnowledgeBaseModel | None
    bedrock_guardrails: BedrockGuardrailsModel | None
    active_models: ActiveModelsModel  # type: ignore

    @staticmethod
    def __is_pinned_format(value: str) -> bool:
        """Check if the value matches the 'pinned@xxx' format."""
        if value.startswith("pinned@"):
            parts = value.split("@")
            return len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 3
        return False

    @field_validator("shared_status")
    def validate_shared_status(cls, value: str) -> str:
        if value in {"unshared", "shared"} or cls.__is_pinned_format(value):
            return value
        raise ValueError(
            f"Invalid shared_status: {value}. Must be 'unshared', 'shared', or 'pinned@xxx' (xxx is a 3-digit integer)."
        )

    @model_validator(mode="after")
    def validate_shared_scope(self) -> Self:
        if self.shared_scope == "private":
            if self.shared_status != "unshared":
                raise ValueError(
                    "shared_status must be 'unshared' when shared_scope is 'private'."
                )
            if self.allowed_cognito_groups or self.allowed_cognito_users:
                raise ValueError(
                    "allowed_cognito_groups and allowed_cognito_users must be empty when shared_scope is 'private'."
                )
        elif self.shared_scope == "partial":
            if self.shared_status == "unshared":
                raise ValueError(
                    "shared_status must be 'shared' or 'pinned@xxx' when shared_scope is 'partial'."
                )
            if not self.allowed_cognito_groups and not self.allowed_cognito_users:
                raise ValueError(
                    "allowed_cognito_groups or allowed_cognito_users must be set when shared_scope is 'partial'."
                )
        elif self.shared_scope == "all":
            if self.shared_status == "unshared":
                raise ValueError(
                    "shared_status must be 'shared' or 'pinned@xxx' when shared_scope is 'all'."
                )
        return self

    @field_validator("published_api_stack_name", mode="after")
    def validate_published_api_stack_name(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        if value is not None:
            if info.data.get("shared_scope") != "all":
                raise ValueError(
                    "published_api_stack_name must be None when shared_scope is not 'all'."
                )
        return value

    def has_knowledge(self) -> bool:
        return (
            len(self.knowledge.source_urls) > 0
            or len(self.knowledge.sitemap_urls) > 0
            or len(self.knowledge.filenames) > 0
            or len(self.knowledge.s3_urls) > 0
            or self.has_bedrock_knowledge_base()
        )

    def is_agent_enabled(self) -> bool:
        return len(self.agent.tools) > 0

    def has_bedrock_knowledge_base(self) -> bool:
        return self.bedrock_knowledge_base is not None and (
            self.bedrock_knowledge_base.knowledge_base_id is not None
            or self.bedrock_knowledge_base.exist_knowledge_base_id is not None
        )

    def is_pinned(self) -> bool:
        return self.shared_status.startswith("pinned@")

    def is_accessible_by_user(self, user: User) -> bool:
        """Check if the bot is accessible by the user. This is used for reading the bot."""
        if user.is_admin() or self.owner_user_id == user.id:
            return True

        if self.shared_scope == "private":
            return False

        if self.shared_scope == "all":
            return True

        if user.id in self.allowed_cognito_users:
            return True

        # Check if the user is in the allowed Cognito groups
        user_groups = get_user_cognito_groups(user)
        return any(group in self.allowed_cognito_groups for group in user_groups)

    def is_editable_by_user(self, user: User) -> bool:
        """Check if the bot is editable by the user. This is used for updating and deleting the bot."""
        if user.is_admin():
            return True

        if self.is_owned_by_user(user):
            return True

        return False

    def is_owned_by_user(self, user: User) -> bool:
        """Check if the bot is owned by the user."""
        return self.owner_user_id == user.id

    @classmethod
    def from_input(
        cls, bot_input: BotInput, owner_user_id: str, knowledge: KnowledgeModel
    ) -> Self:
        """Create a BotModel instance. This is used when creating a new bot."""
        from app.agents.utils import get_tool_by_name

        current_time = get_current_time()

        generation_params: GenerationParamsDict = (
            {
                "max_tokens": bot_input.generation_params.max_tokens,
                "top_k": bot_input.generation_params.top_k,
                "top_p": bot_input.generation_params.top_p,
                "temperature": bot_input.generation_params.temperature,
                "stop_sequences": bot_input.generation_params.stop_sequences,
            }
            if bot_input.generation_params
            else DEFAULT_GENERATION_CONFIG
        )

        agent = (
            AgentModel(
                tools=[
                    AgentToolModel(name=t.name, description=t.description)
                    for t in [
                        get_tool_by_name(tool_name)
                        for tool_name in bot_input.agent.tools
                    ]
                ]
            )
            if bot_input.agent
            else AgentModel(tools=[])
        )

        sync_status: type_sync_status = (
            "QUEUED"
            if bot_input.has_knowledge() or bot_input.has_guardrails()
            else "SUCCEEDED"
        )

        return cls(
            id=bot_input.id,
            owner_user_id=owner_user_id,
            title=bot_input.title,
            description=bot_input.description or "",
            instruction=bot_input.instruction,
            create_time=current_time,
            last_used_time=current_time,
            shared_scope="private",
            shared_status="unshared",
            allowed_cognito_groups=[],
            allowed_cognito_users=[],
            is_starred=False,
            generation_params=GenerationParamsModel(**generation_params),
            agent=agent,
            knowledge=knowledge,
            sync_status=sync_status,
            sync_status_reason="",
            sync_last_exec_id="",
            published_api_stack_name=None,
            published_api_datetime=None,
            published_api_codebuild_id=None,
            display_retrieved_chunks=bot_input.display_retrieved_chunks,
            conversation_quick_starters=(
                []
                if bot_input.conversation_quick_starters is None
                else [
                    ConversationQuickStarterModel(
                        title=starter.title,
                        example=starter.example,
                    )
                    for starter in bot_input.conversation_quick_starters
                ]
            ),
            bedrock_knowledge_base=(
                BedrockKnowledgeBaseModel(
                    **(bot_input.bedrock_knowledge_base.model_dump())
                )
                if bot_input.bedrock_knowledge_base
                else None
            ),
            bedrock_guardrails=(
                BedrockGuardrailsModel(**(bot_input.bedrock_guardrails.model_dump()))
                if bot_input.bedrock_guardrails
                else None
            ),
            active_models=ActiveModelsModel.model_validate(
                bot_input.active_models.model_dump()
            ),
        )

    def to_output(self) -> BotOutput:
        return BotOutput(
            id=self.id,
            title=self.title,
            description=self.description,
            instruction=self.instruction,
            create_time=self.create_time,
            last_used_time=self.last_used_time,
            is_public=self.shared_scope == "all",
            is_starred=self.is_starred,
            owned=True,
            generation_params=GenerationParams.model_validate(
                self.generation_params.model_dump()
            ),
            agent=Agent.model_validate(self.agent.model_dump()),
            knowledge=Knowledge.model_validate(self.knowledge.model_dump()),
            sync_status=self.sync_status,
            sync_status_reason=self.sync_status_reason,
            sync_last_exec_id=self.sync_last_exec_id,
            display_retrieved_chunks=self.display_retrieved_chunks,
            conversation_quick_starters=[
                ConversationQuickStarter.model_validate(starter.model_dump())
                for starter in self.conversation_quick_starters
            ],
            bedrock_knowledge_base=(
                BedrockKnowledgeBaseOutput.model_validate(
                    self.bedrock_knowledge_base.model_dump()
                )
                if self.bedrock_knowledge_base
                else None
            ),
            bedrock_guardrails=(
                BedrockGuardrailsOutput.model_validate(
                    self.bedrock_guardrails.model_dump()
                )
                if self.bedrock_guardrails
                else None
            ),
            active_models=ActiveModelsOutput.model_validate(
                self.active_models.model_dump()
            ),
        )

    def to_summary_output(self, user: User) -> BotSummaryOutput:
        return BotSummaryOutput(
            id=self.id,
            title=self.title,
            description=self.description,
            create_time=self.create_time,
            last_used_time=self.last_used_time,
            is_starred=self.is_starred,
            has_agent=self.is_agent_enabled(),
            owned=self.is_owned_by_user(user),
            sync_status=self.sync_status,
            has_knowledge=self.has_knowledge(),
            conversation_quick_starters=[
                ConversationQuickStarter(
                    title=starter.title,
                    example=starter.example,
                )
                for starter in self.conversation_quick_starters
            ],
            shared_scope=self.shared_scope,
            shared_status=self.shared_status,
            active_models=ActiveModelsOutput.model_validate(
                self.active_models.model_dump()
            ),
        )


class BotAliasModel(BaseModel):
    # TODO: N+1だと不要なものを洗い出す
    # 必須なもの: original_bot_id (N+1取得時), is_origin_accessible
    # Original削除された際にタイトルなどが必要なため、以下は必要
    # title, description
    # その他必要なもの
    # create_time, last_used_time, is_starred, sync_status, has_knowledge, has_agent, conversation_quick_starters
    original_bot_id: str = Field(..., description="Original Bot ID")
    owner_user_id: str = Field(..., description="Owner User ID")
    title: str
    description: str

    is_origin_accessible: bool

    create_time: Float
    last_used_time: Float
    is_starred: bool
    sync_status: type_sync_status
    has_knowledge: bool
    has_agent: bool
    conversation_quick_starters: list[ConversationQuickStarterModel]
    active_models: ActiveModelsModel  # type: ignore

    @classmethod
    def from_bot_for_initial_alias(cls, bot: BotModel) -> Self:
        """Create a BotAliasModel instance. This is used when creating a new alias."""
        current_time = get_current_time()
        return cls(
            original_bot_id=bot.id,
            owner_user_id=bot.owner_user_id,
            title=bot.title,
            description=bot.description,
            is_origin_accessible=True,
            create_time=current_time,
            last_used_time=current_time,
            is_starred=False,
            sync_status=bot.sync_status,
            has_knowledge=bot.has_knowledge(),
            has_agent=bot.is_agent_enabled(),
            conversation_quick_starters=bot.conversation_quick_starters,
            active_models=bot.active_models,
        )


class BotMeta(BaseModel):
    id: str = Field(..., description="Bot ID")
    title: str
    description: str
    create_time: Float
    last_used_time: Float
    is_starred: bool
    sync_status: type_sync_status
    has_bedrock_knowledge_base: bool
    # Whether the bot is owned by the user
    owned: bool

    shared_scope: type_shared_scope
    shared_status: str = Field(
        ..., description="private, shared, or pinned@xxx (xxx is a 3-digit integer)"
    )

    # Whether the bot is available or not.
    # This can be `False` if the bot is not owned by the user and original bot is removed or not permitted to use.
    is_origin_accessible: bool

    # is_public: bool
    # # Whether the bot is available or not.
    # # This can be `False` if the bot is not owned by the user and original bot is removed.
    # available: bool

    @classmethod
    def from_dynamo_item(
        cls,
        item: dict,
        owned: bool,
        is_origin_accessible: bool,
        is_starred: bool | None = None,
    ) -> Self:
        _is_starred: bool = (
            is_starred if is_starred is not None else item.get("IsStarred", False)
        )
        assert (
            item["ItemType"].find("BOT") != -1
        ), f"Invalid ItemType: {item['ItemType']}"
        return cls(
            id=item["BotId"],
            title=item["Title"],
            description=item["Description"],
            create_time=item["CreateTime"],
            last_used_time=item["LastUsedTime"],
            is_starred=_is_starred,
            sync_status=item["SyncStatus"],
            has_bedrock_knowledge_base=bool(item.get("BedrockKnowledgeBase")),
            owned=owned,
            is_origin_accessible=is_origin_accessible,
            shared_scope=item.get("SharedScope", "private"),
            shared_status=item["SharedStatus"],
        )

    @classmethod
    def from_dynamo_alias_item(
        cls,
        item: dict,
        owned: bool,
        is_origin_accessible: bool,
        is_starred: bool | None = None,
    ) -> Self:
        _is_starred: bool = (
            is_starred if is_starred is not None else item.get("IsStarred", False)
        )
        assert (
            item["ItemType"].find("ALIAS") != -1
        ), f"Invalid ItemType: {item['ItemType']}"
        return cls(
            id=item["OriginalBotId"],
            title=item["Title"],
            description=item["Description"],
            create_time=item["CreateTime"],
            last_used_time=item["LastUsedTime"],
            is_starred=_is_starred,
            sync_status=item["SyncStatus"],
            has_bedrock_knowledge_base=bool(item.get("BedrockKnowledgeBase")),
            owned=owned,
            is_origin_accessible=is_origin_accessible,
            shared_scope="private",
            shared_status="unshared",
        )

    def to_output(self) -> BotMetaOutput:
        return BotMetaOutput(
            id=self.id,
            title=self.title,
            description=self.description,
            create_time=self.create_time,
            last_used_time=self.last_used_time,
            is_starred=self.is_starred,
            owned=self.owned,
            available=self.is_origin_accessible,
            sync_status=self.sync_status,
            shared_scope=self.shared_scope,
            shared_status=self.shared_status,
        )


class BotMetaWithStackInfo(BaseModel):
    id: str = Field(..., description="Bot ID")
    title: str
    description: str
    create_time: Float
    last_used_time: Float
    sync_status: type_sync_status
    owner_user_id: str
    published_api_stack_name: str | None
    published_api_datetime: int | None
