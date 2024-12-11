import logging
import os
from typing import Literal

from app.agents.utils import get_available_tools, get_tool_by_name
from app.config import DEFAULT_GENERATION_CONFIG as DEFAULT_CLAUDE_GENERATION_CONFIG
from app.config import DEFAULT_MISTRAL_GENERATION_CONFIG
from app.config import GenerationParams as GenerationParamsDict
from app.repositories.common import RecordNotFoundError, get_bot_table_client
from app.repositories.custom_bot import (
    delete_alias_by_id,
    delete_bot_by_id,
    find_bot_by_id,
    find_owned_bots_by_user_id,
    find_recently_used_bots_by_user_id,
    find_starred_bots_by_user_id,
    store_alias,
    store_bot,
    update_alias_is_origin_accessible,
    update_alias_last_used_time,
    update_alias_star_status,
    update_bot,
    update_bot_last_used_time,
    update_bot_star_status,
)
from app.repositories.models.custom_bot import (
    AgentModel,
    AgentToolModel,
    BotAliasModel,
    BotMeta,
    BotModel,
    ConversationQuickStarterModel,
    GenerationParamsModel,
    KnowledgeModel,
)
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.repositories.models.custom_bot_kb import BedrockKnowledgeBaseModel
from app.routes.schemas.bot import (
    Agent,
    AgentTool,
    BotInput,
    BotMetaOutput,
    BotModifyInput,
    BotModifyOutput,
    BotOutput,
    BotSummaryOutput,
    ConversationQuickStarter,
    GenerationParams,
    Knowledge,
    type_sync_status,
)
from app.routes.schemas.bot_guardrails import BedrockGuardrailsOutput
from app.routes.schemas.bot_kb import BedrockKnowledgeBaseOutput
from app.user import User
from app.utils import (
    compose_upload_document_s3_path,
    compose_upload_temp_s3_path,
    compose_upload_temp_s3_prefix,
    delete_file_from_s3,
    delete_files_with_prefix_from_s3,
    generate_presigned_url,
    get_current_time,
    move_file_in_s3,
)
from boto3.dynamodb.conditions import Attr, Key

logger = logging.getLogger(__name__)

DOCUMENT_BUCKET = os.environ.get("DOCUMENT_BUCKET", "bedrock-documents")
ENABLE_MISTRAL = os.environ.get("ENABLE_MISTRAL", "") == "true"

DEFAULT_GENERATION_CONFIG = (
    DEFAULT_MISTRAL_GENERATION_CONFIG
    if ENABLE_MISTRAL
    else DEFAULT_CLAUDE_GENERATION_CONFIG
)


def _update_s3_documents_by_diff(
    user_id: str,
    bot_id: str,
    added_filenames: list[str],
    deleted_filenames: list[str],
):
    for filename in added_filenames:
        tmp_path = compose_upload_temp_s3_path(user_id, bot_id, filename)
        document_path = compose_upload_document_s3_path(user_id, bot_id, filename)
        move_file_in_s3(DOCUMENT_BUCKET, tmp_path, document_path)

    for filename in deleted_filenames:
        document_path = compose_upload_document_s3_path(user_id, bot_id, filename)
        delete_file_from_s3(DOCUMENT_BUCKET, document_path)


def create_new_bot(user: User, bot_input: BotInput) -> BotOutput:
    """Create a new bot.
    Bot is created as private.
    """

    # Create initial knowledge
    source_urls = []
    sitemap_urls = []
    filenames = []
    s3_urls = []
    if bot_input.knowledge:
        source_urls = bot_input.knowledge.source_urls
        sitemap_urls = bot_input.knowledge.sitemap_urls
        s3_urls = bot_input.knowledge.s3_urls

        # Commit changes to S3
        _update_s3_documents_by_diff(
            user.id, bot_input.id, bot_input.knowledge.filenames, []
        )
        # Delete files from upload temp directory
        delete_files_with_prefix_from_s3(
            DOCUMENT_BUCKET, compose_upload_temp_s3_prefix(user.id, bot_input.id)
        )
        filenames = bot_input.knowledge.filenames

    knowledge = KnowledgeModel(
        source_urls=source_urls,
        sitemap_urls=sitemap_urls,
        filenames=filenames,
        s3_urls=s3_urls,
    )

    new_bot = BotModel.from_input(bot_input, owner_id=user.id, knowledge=knowledge)
    store_bot(new_bot)

    return new_bot.to_output()


def modify_owned_bot(
    user: User, bot_id: str, modify_input: BotModifyInput
) -> BotModifyOutput:
    """Modify owned bot."""
    bot = find_bot_by_id(bot_id)
    if not bot.is_editable_by_user(user):
        raise PermissionError(f"User {user.id} is not authorized to modify bot {bot_id}")

    source_urls = []
    sitemap_urls = []
    filenames = []
    s3_urls = []
    sync_status: type_sync_status = "QUEUED"

    if modify_input.knowledge:
        source_urls = modify_input.knowledge.source_urls
        sitemap_urls = modify_input.knowledge.sitemap_urls
        s3_urls = modify_input.knowledge.s3_urls

        # Commit changes to S3
        _update_s3_documents_by_diff(
            user.id,
            bot_id,
            modify_input.knowledge.added_filenames,
            modify_input.knowledge.deleted_filenames,
        )
        # Delete files from upload temp directory
        delete_files_with_prefix_from_s3(
            DOCUMENT_BUCKET, compose_upload_temp_s3_prefix(user_id, bot_id)
        )

        filenames = (
            modify_input.knowledge.added_filenames
            + modify_input.knowledge.unchanged_filenames
        )

    generation_params: GenerationParamsDict = (
        {
            "max_tokens": modify_input.generation_params.max_tokens,
            "top_k": modify_input.generation_params.top_k,
            "top_p": modify_input.generation_params.top_p,
            "temperature": modify_input.generation_params.temperature,
            "stop_sequences": modify_input.generation_params.stop_sequences,
        }
        if modify_input.generation_params
        else DEFAULT_GENERATION_CONFIG
    )

    agent = (
        AgentModel(
            tools=[
                AgentToolModel(name=t.name, description=t.description)
                for t in [
                    get_tool_by_name(tool_name) for tool_name in modify_input.agent.tools
                ]
            ]
        )
        if modify_input.agent
        else AgentModel(tools=[])
    )

    # if knowledge is not updated, skip embeding process.
    # 'sync_status = "QUEUED"' will execute embeding process and update dynamodb record.
    # 'sync_status= "SUCCEEDED"' will update only dynamodb record.
    sync_status = (
        "QUEUED"
        if modify_input.is_embedding_required(bot)
        or modify_input.is_guardrails_update_required(bot)
        else "SUCCEEDED"
    )

    update_bot(
        user.id,
        bot_id,
        title=modify_input.title,
        instruction=modify_input.instruction,
        description=modify_input.description if modify_input.description else "",
        generation_params=GenerationParamsModel(**generation_params),
        agent=agent,
        knowledge=KnowledgeModel(
            source_urls=source_urls,
            sitemap_urls=sitemap_urls,
            filenames=filenames,
            s3_urls=s3_urls,
        ),
        sync_status=sync_status,
        sync_status_reason="",
        display_retrieved_chunks=modify_input.display_retrieved_chunks,
        conversation_quick_starters=(
            []
            if modify_input.conversation_quick_starters is None
            else [
                ConversationQuickStarterModel(
                    title=starter.title,
                    example=starter.example,
                )
                for starter in modify_input.conversation_quick_starters
            ]
        ),
        bedrock_knowledge_base=(
            BedrockKnowledgeBaseModel(**modify_input.bedrock_knowledge_base.model_dump())
            if modify_input.bedrock_knowledge_base
            else None
        ),
        bedrock_guardrails=(
            BedrockGuardrailsModel(**modify_input.bedrock_guardrails.model_dump())
            if modify_input.bedrock_guardrails
            else None
        ),
    )

    return BotModifyOutput(
        id=bot_id,
        title=modify_input.title,
        instruction=modify_input.instruction,
        description=modify_input.description if modify_input.description else "",
        generation_params=GenerationParams(**generation_params),
        agent=Agent(
            tools=[
                AgentTool(name=tool.name, description=tool.description)
                for tool in agent.tools
            ]
        ),
        knowledge=Knowledge(
            source_urls=source_urls,
            sitemap_urls=sitemap_urls,
            filenames=filenames,
            s3_urls=s3_urls,
        ),
        conversation_quick_starters=(
            []
            if modify_input.conversation_quick_starters is None
            else [
                ConversationQuickStarter(
                    title=starter.title,
                    example=starter.example,
                )
                for starter in modify_input.conversation_quick_starters
            ]
        ),
        bedrock_knowledge_base=(
            BedrockKnowledgeBaseOutput(
                **(modify_input.bedrock_knowledge_base.model_dump())
            )
            if modify_input.bedrock_knowledge_base
            else None
        ),
        bedrock_guardrails=(
            BedrockGuardrailsOutput(**modify_input.bedrock_guardrails.model_dump())
            if modify_input.bedrock_guardrails
            else None
        ),
    )


def fetch_bot(user: User, bot_id: str) -> tuple[bool, BotModel]:
    """Fetch bot by id.
    The first element of the returned tuple is whether the bot is owned or not.
    `True` means the bot is owned by the user.
    `False` means the bot is shared by another user.
    """
    try:
        bot = find_bot_by_id(bot_id)
    except RecordNotFoundError as e:
        # NOTE: If the bot is not found, it must be an alias.
        update_alias_is_origin_accessible(user.id, bot_id, False)
        raise e

    if not bot.is_accessible_by_user(user):
        # NOTE: If the bot is not accessible, it must be an alias.
        update_alias_is_origin_accessible(user.id, bot_id, False)
        raise PermissionError(f"User {user.id} is not authorized to access bot {bot_id}")

    owned = bot.is_owned_by_user(user)

    # Note that `fetch_bot_summary` creates alias.
    # if not owned:
    #     # Update alias to the latest information
    #     store_alias(user_id=user.id, alias=BotAliasModel.from_bot(bot))

    return owned, bot


def fetch_all_bots(
    user: User,
    limit: int | None = None,
    starred: bool = False,
    kind: Literal["private", "mixed"] = "private",
) -> list[BotMetaOutput]:
    """Fetch all bots.
    The order is descending by `last_used_time`.
    - If `kind` is `private`, only private bots will be returned.
        - If `mixed` must give either `starred` or `limit`.
    - If `starred` is True, only starred bots will be returned.
        - When kind is `private`, this will be ignored.
    - If `limit` is specified, only the first n bots will be returned.
        - Cannot specify both `starred` and `limit`.
    """
    # TODO: 複数のメソッドに分けてリプレースする。
    # private: 自分が作成したボットの一覧
    # mixed: 自分が作成したボットと共有されたボットの一覧
    #   - pinned: ピン留めされたボットのみ。スターをつけたボット（とエイリアス）
    #   - limit: 最新のn個のボットのみ。最近使った自分のボットと、共有ボットの取得に使う
    #     NOTE: FE側で、自分のボットを含むかどうかを判断している
    #     i.e. 「最近使用したボット」と「最近使用した公開ボット」は同時に取得
    #     ref: useBot.tsの
    #       recentlyUsedSharedBots: recentlyUsedBots?.filter((bot) => !bot.owned),

    if not starred and not limit:
        raise ValueError("Must specify either `limit` or `starred`")
    if limit and starred:
        raise ValueError("Cannot specify both `limit` and `starred`")
    if limit and (limit < 0 or limit > 100):
        raise ValueError("Limit must be between 0 and 100")

    bots = []
    if kind == "private":
        # Fetch only private owned bots by user
        bots = find_owned_bots_by_user_id(user.id, limit=limit)
    elif kind == "mixed":
        if starred:
            # Fetch starred bots
            bots = find_starred_bots_by_user_id(user.id, limit=limit)
        else:
            # Fetch recently used bots
            bots = find_recently_used_bots_by_user_id(user.id, limit=limit)

    bot_metas = []
    for bot in bots:
        if not bot.has_bedrock_knowledge_base:
            # Created bots under major version 1.4~, 2~ should have bedrock knowledge base.
            # If the bot does not have bedrock knowledge base,
            # it is not shown in the list.
            continue
        bot_metas.append(bot.to_output())
    return bot_metas


def fetch_bot_summary(user: User, bot_id: str) -> BotSummaryOutput:
    bot = find_bot_by_id(bot_id)
    if not bot.is_accessible_by_user(user):
        raise PermissionError(f"User {user.id} is not authorized to access bot {bot_id}")

    if not bot.is_owned_by_user(user):
        # NOTE: At the first time using shared bot, alias is not created yet.
        store_alias(user_id=user.id, alias=BotAliasModel.from_bot(bot))

    try:
        bot = find_private_bot_by_id(user_id, bot_id)
        return BotSummaryOutput(
            id=bot_id,
            title=bot.title,
            description=bot.description,
            create_time=bot.create_time,
            last_used_time=bot.last_used_time,
            is_starred=bot.is_starred,
            is_public=True if bot.public_bot_id else False,
            has_agent=bot.is_agent_enabled(),
            owned=True,
            sync_status=bot.sync_status,
            has_knowledge=bot.has_knowledge(),
            conversation_quick_starters=[
                ConversationQuickStarter(
                    title=starter.title,
                    example=starter.example,
                )
                for starter in bot.conversation_quick_starters
            ],
        )

    except RecordNotFoundError:
        pass

    try:
        alias = find_alias_by_id(user_id, bot_id)
        return BotSummaryOutput(
            id=alias.id,
            title=alias.title,
            description=alias.description,
            create_time=alias.create_time,
            last_used_time=alias.last_used_time,
            is_starred=alias.is_starred,
            is_public=True,
            has_agent=alias.has_agent,
            owned=False,
            sync_status=alias.sync_status,
            has_knowledge=alias.has_knowledge,
            conversation_quick_starters=(
                []
                if alias.conversation_quick_starters is None
                else [
                    ConversationQuickStarter(
                        title=starter.title,
                        example=starter.example,
                    )
                    for starter in alias.conversation_quick_starters
                ]
            ),
        )
    except RecordNotFoundError:
        pass

    try:
        # NOTE: At the first time using shared bot, alias is not created yet.
        bot = find_public_bot_by_id(bot_id)
        current_time = get_current_time()
        # Store alias when opened shared bot page
        store_alias(
            user_id,
            BotAliasModel(
                id=bot.id,
                title=bot.title,
                description=bot.description,
                original_bot_id=bot_id,
                create_time=current_time,
                last_used_time=current_time,
                is_starred=False,
                sync_status=bot.sync_status,
                has_knowledge=bot.has_knowledge(),
                has_agent=bot.is_agent_enabled(),
                conversation_quick_starters=[
                    ConversationQuickStarterModel(
                        title=starter.title,
                        example=starter.example,
                    )
                    for starter in bot.conversation_quick_starters
                ],
            ),
        )
        return BotSummaryOutput(
            id=bot_id,
            title=bot.title,
            description=bot.description,
            create_time=bot.create_time,
            last_used_time=bot.last_used_time,
            is_starred=False,  # NOTE: Shared bot is not pinned by default.
            is_public=True,
            has_agent=bot.is_agent_enabled(),
            owned=False,
            sync_status=bot.sync_status,
            has_knowledge=bot.has_knowledge(),
            conversation_quick_starters=[
                ConversationQuickStarter(
                    title=starter.title,
                    example=starter.example,
                )
                for starter in bot.conversation_quick_starters
            ],
        )
    except RecordNotFoundError:
        raise RecordNotFoundError(
            f"Bot with ID {bot_id} not found in both private (for user {user_id}) and alias, shared items."
        )


def modify_pin_status(user: User, bot_id: str, pinned: bool):
    """Modify bot pin status."""
    try:
        return update_bot_star_status(user.id, bot_id, pinned)
    except RecordNotFoundError:
        pass

    try:
        return update_alias_star_status(user.id, bot_id, pinned)
    except RecordNotFoundError:
        raise RecordNotFoundError(f"Bot {bot_id} is neither owned nor alias.")


def remove_bot_by_id(user: User, bot_id: str):
    """Remove bot by id."""
    try:
        return delete_bot_by_id(user_id, bot_id)
    except RecordNotFoundError:
        pass

    try:
        return delete_alias_by_id(user_id, bot_id)
    except RecordNotFoundError:
        raise RecordNotFoundError(f"Bot {bot_id} is neither owned nor alias.")


def modify_bot_last_used_time(user: User, bot_id: str):
    """Modify bot last used time."""
    try:
        return update_bot_last_used_time(user_id, bot_id)
    except RecordNotFoundError:
        pass

    try:
        return update_alias_last_used_time(user_id, bot_id)
    except RecordNotFoundError:
        raise RecordNotFoundError(f"Bot {bot_id} is neither owned nor alias.")


def issue_presigned_url(user: User, bot_id: str, filename: str, content_type: str) -> str:
    response = generate_presigned_url(
        DOCUMENT_BUCKET,
        compose_upload_temp_s3_path(user_id, bot_id, filename),
        content_type=content_type,
        expiration=3600,
        client_method="put_object",
    )
    return response


def remove_uploaded_file(user: User, bot_id: str, filename: str):
    delete_file_from_s3(
        DOCUMENT_BUCKET, compose_upload_temp_s3_path(user_id, bot_id, filename)
    )
    return


def fetch_available_agent_tools():
    """Fetch available tools for bot."""
    return get_available_tools()
