import asyncio
import base64
import json
import logging
import os
from decimal import Decimal as decimal
from functools import partial

from app.config import DEFAULT_GENERATION_CONFIG as DEFAULT_CLAUDE_GENERATION_CONFIG
from app.config import DEFAULT_MISTRAL_GENERATION_CONFIG
from app.repositories.common import (
    TRANSACTION_BATCH_READ_SIZE,
    RecordNotFoundError,
    compose_item_type,
    compose_sk,
    get_bot_table_client,
)
from app.repositories.models.custom_bot import (
    AgentModel,
    BotAliasModel,
    BotMeta,
    BotMetaWithStackInfo,
    BotModel,
    ConversationQuickStarterModel,
    GenerationParamsModel,
    KnowledgeModel,
)
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.repositories.models.custom_bot_kb import BedrockKnowledgeBaseModel
from app.routes.schemas.bot import type_shared_scope, type_sync_status
from app.utils import get_current_time
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

ENABLE_MISTRAL = os.environ.get("ENABLE_MISTRAL", "") == "true"

DEFAULT_GENERATION_CONFIG = (
    DEFAULT_MISTRAL_GENERATION_CONFIG
    if ENABLE_MISTRAL
    else DEFAULT_CLAUDE_GENERATION_CONFIG
)

logger = logging.getLogger(__name__)


class BotNotFoundException(Exception):
    """Exception raised when a bot is not found."""

    pass


class BotUpdateError(Exception):
    """Exception raised when there's an error updating a bot."""

    pass


def store_bot(custom_bot: BotModel):
    table = get_bot_table_client()
    logger.info(f"Storing bot: {custom_bot}")

    item = {
        "PK": custom_bot.owner_id,
        "SK": compose_sk(custom_bot.id, "bot"),
        "ItemType": compose_item_type(custom_bot.owner_id, "bot"),
        "Title": custom_bot.title,
        "Description": custom_bot.description,
        "Instruction": custom_bot.instruction,
        "CreateTime": decimal(custom_bot.create_time),
        "BotId": custom_bot.id,
        "SharedScope": custom_bot.shared_scope,
        "SharedStatus": custom_bot.shared_status,
        "AllowedCognitoGroups": custom_bot.allowed_cognito_groups,
        "AllowedCognitoUsers": custom_bot.allowed_cognito_users,
        "LastUsedTime": decimal(custom_bot.last_used_time),
        "GenerationParams": custom_bot.generation_params.model_dump(),
        "AgentData": custom_bot.agent.model_dump(),
        "Knowledge": custom_bot.knowledge.model_dump(),
        "SyncStatus": custom_bot.sync_status,
        "SyncStatusReason": custom_bot.sync_status_reason,
        "LastExecId": custom_bot.sync_last_exec_id,
        "ApiPublishmentStackName": custom_bot.published_api_stack_name,
        "ApiPublishedDatetime": custom_bot.published_api_datetime,
        "ApiPublishCodeBuildId": custom_bot.published_api_codebuild_id,
        "DisplayRetrievedChunks": custom_bot.display_retrieved_chunks,
        "ConversationQuickStarters": [
            starter.model_dump() for starter in custom_bot.conversation_quick_starters
        ],
    }

    if custom_bot.is_starred:
        # To use sparse index, set `IsStarred` attribute only when it's starred
        item["IsStarred"] = "TRUE"
    if custom_bot.bedrock_knowledge_base:
        item["BedrockKnowledgeBase"] = custom_bot.bedrock_knowledge_base.model_dump()
    if custom_bot.bedrock_guardrails:
        item["GuardrailsParams"] = custom_bot.bedrock_guardrails.model_dump()

    response = table.put_item(Item=item)
    return response


def update_bot(
    owner_id: str,
    bot_id: str,
    title: str,
    description: str,
    instruction: str,
    generation_params: GenerationParamsModel,
    agent: AgentModel,
    knowledge: KnowledgeModel,
    sync_status: type_sync_status,
    sync_status_reason: str,
    display_retrieved_chunks: bool,
    conversation_quick_starters: list[ConversationQuickStarterModel],
    bedrock_knowledge_base: BedrockKnowledgeBaseModel | None = None,
    bedrock_guardrails: BedrockGuardrailsModel | None = None,
):
    """Update bot title, description, and instruction.
    NOTE: Use `update_bot_visibility` to update visibility.
    """
    table = get_bot_table_client()
    logger.info(f"Updating bot: {bot_id}")

    update_expression = (
        "SET Title = :title, "
        "Description = :description, "
        "Instruction = :instruction, "
        "AgentData = :agent_data, "
        "Knowledge = :knowledge, "
        "SyncStatus = :sync_status, "
        "SyncStatusReason = :sync_status_reason, "
        "GenerationParams = :generation_params, "
        "DisplayRetrievedChunks = :display_retrieved_chunks, "
        "ConversationQuickStarters = :conversation_quick_starters"
    )

    expression_attribute_values = {
        ":title": title,
        ":description": description,
        ":instruction": instruction,
        ":knowledge": knowledge.model_dump(),
        ":agent_data": agent.model_dump(),
        ":sync_status": sync_status,
        ":sync_status_reason": sync_status_reason,
        ":display_retrieved_chunks": display_retrieved_chunks,
        ":generation_params": generation_params.model_dump(),
        ":conversation_quick_starters": [
            starter.model_dump() for starter in conversation_quick_starters
        ],
    }
    if bedrock_knowledge_base:
        update_expression += ", BedrockKnowledgeBase = :bedrock_knowledge_base"
        expression_attribute_values[":bedrock_knowledge_base"] = (
            bedrock_knowledge_base.model_dump()
        )

    if bedrock_guardrails:
        update_expression += ", GuardrailsParams = :bedrock_guardrails"
        expression_attribute_values[":bedrock_guardrails"] = (
            bedrock_guardrails.model_dump()
        )

    try:
        response = table.update_item(
            Key={"PK": owner_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def store_alias(user_id: str, alias: BotAliasModel):
    table = get_bot_table_client()
    logger.info(f"Storing alias: {alias}")

    item = {
        "PK": user_id,
        "SK": compose_sk(alias.original_bot_id, "alias"),
        "ItemType": compose_item_type(user_id, "alias"),
        "IsOriginAccessible": alias.is_origin_accessible,
        "CreateTime": decimal(alias.create_time),
        "LastUsedTime": decimal(alias.last_used_time),
        "IsStarred": alias.is_starred,
        "Title": alias.title,
        "Description": alias.description,
        "SyncStatus": alias.sync_status,
        "HasKnowledge": alias.has_knowledge,
        "HasAgent": alias.has_agent,
        "ConversationQuickStarters": [
            starter.model_dump() for starter in alias.conversation_quick_starters
        ],
    }

    response = table.put_item(Item=item)
    return response


def update_bot_last_used_time(user_id: str, bot_id: str):
    """Update last used time for bot."""
    table = get_bot_table_client()
    logger.info(f"Updating last used time for bot: {bot_id}")
    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET LastUsedTime = :val",
            ExpressionAttributeValues={":val": decimal(get_current_time())},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e
    return response


def update_alias_last_used_time(user_id: str, alias_id: str):
    """Update last used time for alias."""
    table = get_bot_table_client()
    logger.info(f"Updating last used time for alias: {alias_id}")
    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(alias_id, "alias")},
            UpdateExpression="SET LastUsedTime = :val",
            ExpressionAttributeValues={":val": decimal(get_current_time())},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Alias with id {alias_id} not found")
        else:
            raise e
    return response


def update_bot_star_status(user_id: str, bot_id: str, starred: bool):
    """Update starred status for bot."""
    table = get_bot_table_client()
    logger.info(f"Updating starred status for bot: {bot_id}")
    val = "TRUE" if starred else None
    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET IsStarred = :val",
            ExpressionAttributeValues={":val": val},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e
    return response


def update_alias_star_status(user_id: str, alias_id: str, starred: bool):
    """Update starred status for alias."""
    table = get_bot_table_client()
    logger.info(f"Updating starred status for alias: {alias_id}")
    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(alias_id, "alias")},
            UpdateExpression="SET IsStarred = :val",
            ExpressionAttributeValues={":val": starred},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Alias with id {alias_id} not found")
        else:
            raise e
    return response


def update_knowledge_base_id(
    user_id: str, bot_id: str, knowledge_base_id: str, data_source_ids: list[str]
):
    table = get_bot_table_client()
    logger.info(f"Updating knowledge base id for bot: {bot_id}")

    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET BedrockKnowledgeBase.knowledge_base_id = :kb_id, BedrockKnowledgeBase.data_source_ids = :ds_ids",
            ExpressionAttributeValues={
                ":kb_id": knowledge_base_id,
                ":ds_ids": data_source_ids,
            },
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ReturnValues="ALL_NEW",
        )
        logger.info(f"Updated knowledge base id for bot: {bot_id} successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def update_guardrails_params(
    user_id: str, bot_id: str, guardrail_arn: str, guardrail_version: str
):
    logger.info("update_guardrails_params")
    table = get_bot_table_client()

    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET GuardrailsParams.guardrail_arn = :guardrail_arn, GuardrailsParams.guardrail_version = :guardrail_version",
            ExpressionAttributeValues={
                ":guardrail_arn": guardrail_arn,
                ":guardrail_version": guardrail_version,
            },
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ReturnValues="ALL_NEW",
        )
        logger.info(f"Updated guardrails_arn for bot: {bot_id} successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def update_bot_shared_status(
    owner_id: str, bot_id: str, shared_scope: type_shared_scope | None, shared_status: str
):
    """Update shared status for bot."""
    table = get_bot_table_client()
    logger.info(f"Updating shared status for bot: {bot_id}")

    try:
        response = table.update_item(
            Key={"PK": owner_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET SharedScope = :shared_scope, SharedStatus = :shared_status",
            ExpressionAttributeValues={
                ":shared_scope": shared_scope,
                ":shared_status": shared_status,
            },
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ReturnValues="ALL_NEW",
        )
        logger.info(f"Updated shared status for bot: {bot_id} successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e
    return response


def update_alias_is_origin_accessible(
    user_id: str, alias_id: str, is_origin_accessible: bool
):
    """Update is_origin_accessible for alias."""
    table = get_bot_table_client()
    logger.info(f"Updating is_origin_accessible for alias: {alias_id}")
    try:
        response = table.update_item(
            Key={"PK": user_id, "SK": compose_sk(alias_id, "alias")},
            UpdateExpression="SET IsOriginAccessible = :val",
            ExpressionAttributeValues={":val": is_origin_accessible},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Alias with id {alias_id} not found")
        else:
            raise e
    return response


def find_owned_bots_by_user_id(user_id: str, limit: int | None = None) -> list[BotMeta]:
    """Find all owned bots by user id.
    The order is descending by `last_used_time`.
    """
    table = get_bot_table_client()
    logger.info(f"Finding bots for user: {user_id}")

    query_params = {
        "IndexName": "ItemTypeIndex",
        "KeyConditionExpression": Key("ItemType").eq(compose_item_type(user_id, "bot")),
        "ScanIndexForward": False,
    }

    bots = []
    query_count = 0
    MAX_QUERY_COUNT = 5

    while query_count < MAX_QUERY_COUNT:
        query_count += 1
        response = table.query(**query_params)
        bots.extend(
            BotMeta.from_dynamo_item(item, owned=True, is_origin_accessible=True)
            for item in response["Items"]
        )

        if limit and len(bots) >= limit:
            break
        if "LastEvaluatedKey" not in response:
            break
        query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    if query_count == MAX_QUERY_COUNT:
        logger.warning("There are more bots than the query limit.")

    if limit:
        bots = bots[:limit]

    logger.info(f"Found all owned {len(bots)} bots.")
    return bots


def __find_bots_with_condition(
    query_params: dict,
    max_query_count: int = 5,
) -> list[BotMeta]:
    """Find all bots with the given query parameters.
    Process summary:
    1. Query bots with the given query parameters.
    2. Separate bots and aliases.
    3. Process direct bot items.
    4. Process aliases. batch get their original bots using dynamo batch get item.
    5. If original bot is not found, create a BotMeta object with `is_origin_accessible=False`.
    """
    table = get_bot_table_client()
    bots = []
    query_count = 0

    while query_count < max_query_count:
        query_count += 1
        response = table.query(**query_params)

        # Separate bots and aliases
        bot_items = []
        alias_items = []
        for item in response["Items"]:
            if item["ItemType"].find("BOT") != -1:  # Bot
                bot_items.append(item)
            else:  # Alias
                alias_items.append(item)

        # Process direct bot items
        for item in bot_items:
            bots.append(
                BotMeta.from_dynamo_item(item, owned=True, is_origin_accessible=True)
            )

        # Process aliases. batch get their original bots
        if alias_items:
            original_bot_ids = [item["OriginalBotId"] for item in alias_items]

            for i in range(0, len(original_bot_ids), TRANSACTION_BATCH_READ_SIZE):
                batch_ids = original_bot_ids[i : i + TRANSACTION_BATCH_READ_SIZE]
                original_bots_response = table.batch_get_item(
                    RequestItems={
                        table.table_name: {
                            "Keys": [{"BotId": bot_id} for bot_id in batch_ids],
                            "IndexName": "BotIdIndex",
                        }
                    }
                )

                # Create a map of original bot details
                original_bot_map = {
                    item["BotId"]: item
                    for item in original_bots_response["Responses"][table.table_name]
                }

                # Create BotMeta objects for aliases
                for alias in alias_items[i : i + TRANSACTION_BATCH_READ_SIZE]:
                    original_bot = original_bot_map.get(alias["OriginalBotId"])
                    if original_bot:
                        bots.append(
                            BotMeta.from_dynamo_item(
                                original_bot,
                                owned=False,
                                is_origin_accessible=original_bot["SharedScope"] == "all",
                            )
                        )
                    else:
                        # If original bot is not found, create a BotMeta object with `is_origin_accessible=False`
                        bots.append(
                            BotMeta.from_dynamo_item(
                                alias, owned=False, is_origin_accessible=False
                            )
                        )

        if "LastEvaluatedKey" not in response:
            break
        query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    if query_count == max_query_count:
        logger.warning("There are more bots than the query limit.")

    return bots


def find_starred_bots_by_user_id(user_id: str, limit: int | None = None) -> list[BotMeta]:
    """Find all starred bots by user id."""
    logger.info(f"Finding starred bots for user: {user_id}")

    query_params = {
        "IndexName": "StarredIndex",
        "KeyConditionExpression": Key("PK").eq(user_id) & Key("IsStarred").eq("TRUE"),
    }

    bots = __find_bots_with_condition(query_params)

    # Sort bots by last used time
    bots.sort(key=lambda x: x.last_used_time, reverse=True)
    if limit:
        bots = bots[:limit]

    logger.info(f"Found all starred {len(bots)} bots.")
    return bots


def find_recently_used_bots_by_user_id(
    user_id: str, limit: int | None = None
) -> list[BotMeta]:
    """Find all recently used bots by user id."""
    logger.info(f"Finding recently used bots for user: {user_id}")

    query_params = {
        "IndexName": "LastUsedTimeIndex",
        "KeyConditionExpression": Key("PK").eq(user_id),
        "ScanIndexForward": False,
    }

    bots = __find_bots_with_condition(query_params)
    if limit:
        bots = bots[:limit]

    logger.info(f"Found all recently used {len(bots)} bots.")
    return bots


def find_bot_by_id(bot_id: str) -> BotModel:
    table = get_bot_table_client()
    logger.info(f"Finding bot with id: {bot_id}")
    response = table.query(
        IndexName="BotIdIndex", KeyConditionExpression=Key("BotId").eq(bot_id)
    )

    if len(response["Items"]) == 0:
        raise RecordNotFoundError(f"Bot with id {bot_id} not found")

    item = response["Items"][0]

    bot = BotModel(
        id=item["BotId"],
        owner_id=item["PK"],
        title=item["Title"],
        description=item["Description"],
        instruction=item["Instruction"],
        create_time=float(item["CreateTime"]),
        last_used_time=float(item["LastUsedTime"]),
        shared_scope=item.get("SharedScope", None),
        shared_status=item["SharedStatus"],
        allowed_cognito_groups=item.get("AllowedCognitoGroups", []),
        allowed_cognito_users=item.get("AllowedCognitoUsers", []),
        is_starred=item["IsStarred"],
        generation_params=GenerationParamsModel.model_validate(
            item["GenerationParams"]
            if "GenerationParams" in item
            else DEFAULT_GENERATION_CONFIG
        ),
        agent=(
            AgentModel(**item["AgentData"])
            if "AgentData" in item
            else AgentModel(tools=[])
        ),
        knowledge=KnowledgeModel(
            **{**item["Knowledge"], "s3_urls": item["Knowledge"].get("s3_urls", [])}
        ),
        sync_status=item["SyncStatus"],
        sync_status_reason=item["SyncStatusReason"],
        sync_last_exec_id=item["LastExecId"],
        published_api_stack_name=item.get("ApiPublishmentStackName", None),
        published_api_datetime=item.get("ApiPublishedDatetime", None),
        published_api_codebuild_id=item.get("ApiPublishCodeBuildId", None),
        display_retrieved_chunks=item.get("DisplayRetrievedChunks", False),
        conversation_quick_starters=item.get("ConversationQuickStarters", []),
        bedrock_knowledge_base=(
            BedrockKnowledgeBaseModel(
                **{
                    **item["BedrockKnowledgeBase"],
                    "chunking_configuration": item["BedrockKnowledgeBase"].get(
                        "chunking_configuration", None
                    ),
                }
            )
            if "BedrockKnowledgeBase" in item
            else None
        ),
        bedrock_guardrails=(
            BedrockGuardrailsModel(**item["GuardrailsParams"])
            if "GuardrailsParams" in item
            else None
        ),
    )

    logger.info(f"Found bot: {bot}")
    return bot


# TODO: delete
# def find_private_bot_by_id(user_id: str, bot_id: str) -> BotModel:
#     """Find private bot."""
#     table = get_bot_table_client()
#     logger.info(f"Finding bot with id: {bot_id}")
#     response = table.query(
#         IndexName="SKIndex",
#         KeyConditionExpression=Key("SK").eq(compose_bot_id(user_id, bot_id)),
#     )
#     if len(response["Items"]) == 0:
#         raise RecordNotFoundError(f"Bot with id {bot_id} not found")
#     item = response["Items"][0]

#     if "OriginalBotId" in item:
#         raise RecordNotFoundError(f"Bot with id {bot_id} is alias")

#     bot = BotModel(
#         id=decompose_bot_id(item["SK"]),
#         title=item["Title"],
#         description=item["Description"],
#         instruction=item["Instruction"],
#         create_time=float(item["CreateTime"]),
#         last_used_time=float(item["LastUsedTime"]),
#         is_starred=item["IsStarred"],
#         public_bot_id=None if "PublicBotId" not in item else item["PublicBotId"],
#         owner_user_id=user_id,
#         generation_params=GenerationParamsModel.model_validate(
#             item["GenerationParams"]
#             if "GenerationParams" in item
#             else DEFAULT_GENERATION_CONFIG
#         ),
#         agent=(
#             AgentModel(**item["AgentData"])
#             if "AgentData" in item
#             else AgentModel(tools=[])
#         ),
#         knowledge=KnowledgeModel(
#             **{**item["Knowledge"], "s3_urls": item["Knowledge"].get("s3_urls", [])}
#         ),
#         sync_status=item["SyncStatus"],
#         sync_status_reason=item["SyncStatusReason"],
#         sync_last_exec_id=item["LastExecId"],
#         published_api_stack_name=(
#             None
#             if "ApiPublishmentStackName" not in item
#             else item["ApiPublishmentStackName"]
#         ),
#         published_api_datetime=(
#             None if "ApiPublishedDatetime" not in item else item["ApiPublishedDatetime"]
#         ),
#         published_api_codebuild_id=(
#             None if "ApiPublishCodeBuildId" not in item else item["ApiPublishCodeBuildId"]
#         ),
#         display_retrieved_chunks=item.get("DisplayRetrievedChunks", False),
#         conversation_quick_starters=item.get("ConversationQuickStarters", []),
#         bedrock_knowledge_base=(
#             BedrockKnowledgeBaseModel(
#                 **{
#                     **item["BedrockKnowledgeBase"],
#                     "chunking_configuration": item["BedrockKnowledgeBase"].get(
#                         "chunking_configuration", None
#                     ),
#                 }
#             )
#             if "BedrockKnowledgeBase" in item
#             else None
#         ),
#         bedrock_guardrails=(
#             BedrockGuardrailsModel(**item["GuardrailsParams"])
#             if "GuardrailsParams" in item
#             else None
#         ),
#     )

#     logger.info(f"Found bot: {bot}")
#     return bot


# def find_public_bot_by_id(bot_id: str) -> BotModel:
#     """Find public bot by id."""
#     table = get_bot_table_client()  # Use public client
#     logger.info(f"Finding public bot with id: {bot_id}")
#     response = table.query(
#         IndexName="PublicBotIdIndex",
#         KeyConditionExpression=Key("PublicBotId").eq(bot_id),
#     )
#     if len(response["Items"]) == 0:
#         raise RecordNotFoundError(f"Public bot with id {bot_id} not found")

#     item = response["Items"][0]
#     bot = BotModel(
#         id=decompose_bot_id(item["SK"]),
#         title=item["Title"],
#         description=item["Description"],
#         instruction=item["Instruction"],
#         create_time=float(item["CreateTime"]),
#         last_used_time=float(item["LastUsedTime"]),
#         is_starred=item["IsStarred"],
#         public_bot_id=item["PublicBotId"],
#         owner_user_id=item["PK"],
#         generation_params=GenerationParamsModel.model_validate(
#             item["GenerationParams"]
#             if "GenerationParams" in item
#             else DEFAULT_GENERATION_CONFIG
#         ),
#         agent=(
#             AgentModel(**item["AgentData"])
#             if "AgentData" in item
#             else AgentModel(tools=[])
#         ),
#         knowledge=KnowledgeModel(
#             **{**item["Knowledge"], "s3_urls": item["Knowledge"].get("s3_urls", [])}
#         ),
#         sync_status=item["SyncStatus"],
#         sync_status_reason=item["SyncStatusReason"],
#         sync_last_exec_id=item["LastExecId"],
#         published_api_stack_name=(
#             None
#             if "ApiPublishmentStackName" not in item
#             else item["ApiPublishmentStackName"]
#         ),
#         published_api_datetime=(
#             None if "ApiPublishedDatetime" not in item else item["ApiPublishedDatetime"]
#         ),
#         published_api_codebuild_id=(
#             None if "ApiPublishCodeBuildId" not in item else item["ApiPublishCodeBuildId"]
#         ),
#         display_retrieved_chunks=item.get("DisplayRetrievedChunks", False),
#         conversation_quick_starters=item.get("ConversationQuickStarters", []),
#         bedrock_knowledge_base=(
#             BedrockKnowledgeBaseModel(
#                 **{
#                     **item["BedrockKnowledgeBase"],
#                     "chunking_configuration": item["BedrockKnowledgeBase"].get(
#                         "chunking_configuration", None
#                     ),
#                 }
#             )
#             if "BedrockKnowledgeBase" in item
#             else None
#         ),
#         bedrock_guardrails=(
#             BedrockGuardrailsModel(**item["GuardrailsParams"])
#             if "GuardrailsParams" in item
#             else None
#         ),
#     )
#     logger.info(f"Found public bot: {bot}")
#     return bot


# def find_alias_by_id(user_id: str, alias_id: str) -> BotAliasModel:
#     # TODO: 削除を検討 -> prepare_conversationで、初回会話時にのチェックで使われているので必要。存在チェックだけで良い
#     """Find alias bot by id."""
#     table = get_bot_table_client()
#     logger.info(f"Finding alias bot with id: {alias_id}")
#     response = table.query(
#         IndexName="SKIndex",
#         KeyConditionExpression=Key("SK").eq(compose_bot_alias_id(user_id, alias_id)),
#     )
#     if len(response["Items"]) == 0:
#         raise RecordNotFoundError(f"Alias bot with id {alias_id} not found")
#     item = response["Items"][0]

#     bot = BotAliasModel(
#         id=decompose_bot_alias_id(item["SK"]),
#         title=item["Title"],
#         description=item["Description"],
#         original_bot_id=item["OriginalBotId"],
#         create_time=float(item["CreateTime"]),
#         last_used_time=float(item["LastUsedTime"]),
#         is_starred=item["IsStarred"],
#         sync_status=item["SyncStatus"],
#         has_knowledge=item["HasKnowledge"],
#         has_agent=item.get("HasAgent", False),
#         conversation_quick_starters=item.get("ConversationQuickStarters", []),
#     )

#     logger.info(f"Found alias: {bot}")
#     return bot


def update_bot_publication(
    owner_id: str, bot_id: str, published_api_id: str, build_id: str
):
    table = get_bot_table_client()
    current_time = get_current_time()  # epoch time (int) を取得
    logger.info(f"Updating bot publication: {bot_id}")
    try:
        response = table.update_item(
            Key={"PK": owner_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="SET ApiPublishmentStackName = :val, ApiPublishedDatetime = :time, ApiPublishCodeBuildId = :build_id",
            # NOTE: Stack naming rule: ApiPublishmentStack{published_api_id}.
            # See bedrock-chat-stack.ts > `ApiPublishmentStack`
            ExpressionAttributeValues={
                ":val": f"ApiPublishmentStack{published_api_id}",
                ":time": current_time,
                ":build_id": build_id,
            },
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def delete_bot_publication(owner_id: str, bot_id: str):
    table = get_bot_table_client()
    logger.info(f"Deleting bot publication: {bot_id}")
    try:
        response = table.update_item(
            Key={"PK": owner_id, "SK": compose_sk(bot_id, "bot")},
            UpdateExpression="REMOVE ApiPublishmentStackName, ApiPublishedDatetime, ApiPublishCodeBuildId",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def delete_bot_by_id(owner_id: str, bot_id: str):
    table = get_bot_table_client()
    logger.info(f"Deleting bot with id: {bot_id}")

    try:
        response = table.delete_item(
            Key={"PK": owner_id, "SK": compose_sk(bot_id, "bot")},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot with id {bot_id} not found")
        else:
            raise e

    return response


def delete_alias_by_id(user_id: str, bot_id: str):
    table = get_bot_table_client()
    logger.info(f"Deleting alias with id: {bot_id}")

    try:
        response = table.delete_item(
            Key={"PK": user_id, "SK": compose_sk(bot_id, "alias")},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RecordNotFoundError(f"Bot alias with id {bot_id} not found")
        else:
            raise e

    return response


async def find_public_bots_by_ids(bot_ids: list[str]) -> list[BotMetaWithStackInfo]:
    """Find all public bots by ids. This method is intended for administrator use."""
    table = get_bot_table_client()
    loop = asyncio.get_running_loop()

    def query_dynamodb(table, bot_id):
        response = table.query(
            IndexName="BotIdIndex",
            KeyConditionExpression=Key("BotId").eq(bot_id),
        )
        return response["Items"]

    tasks = [
        loop.run_in_executor(None, partial(query_dynamodb, table, bot_id))
        for bot_id in bot_ids
    ]
    results = await asyncio.gather(*tasks)

    bots = []
    for items in results:
        for item in items:
            bots.append(
                BotMetaWithStackInfo(
                    id=item["BotId"],
                    title=item["Title"],
                    description=item["Description"],
                    create_time=float(item["CreateTime"]),
                    last_used_time=float(item["LastUsedTime"]),
                    sync_status=item["SyncStatus"],
                    owner_user_id=item["PK"],
                    published_api_stack_name=item.get("ApiPublishmentStackName", None),
                    published_api_datetime=item.get("ApiPublishedDatetime", None),
                )
            )

    return bots


def find_all_published_bots(
    limit: int = 1000, next_token: str | None = None
) -> tuple[list[BotMetaWithStackInfo], str | None]:
    table = get_bot_table_client()
    query_params = {
        "IndexName": "SharedScopeIndex",
        "KeyConditionExpression": Key("SharedScope").eq("all"),
        "FilterExpression": Attr("ApiPublishmentStackName").exists()
        & Attr("ApiPublishmentStackName").ne(None),
        "Limit": limit,
    }
    if next_token:
        query_params["ExclusiveStartKey"] = json.loads(
            base64.b64decode(next_token).decode("utf-8")
        )

    response = table.query(**query_params)

    bots = [
        BotMetaWithStackInfo(
            id=item["BotId"],
            title=item["Title"],
            description=item["Description"],
            create_time=float(item["CreateTime"]),
            last_used_time=float(item["LastUsedTime"]),
            sync_status=item["SyncStatus"],
            owner_user_id=item["PK"],
            published_api_stack_name=item.get("ApiPublishmentStackName", None),
            published_api_datetime=item.get("ApiPublishedDatetime", None),
        )
        for item in response["Items"]
    ]

    next_token = None
    if "LastEvaluatedKey" in response:
        next_token = base64.b64encode(
            json.dumps(response["LastEvaluatedKey"]).encode("utf-8")
        ).decode("utf-8")

    return bots, next_token
