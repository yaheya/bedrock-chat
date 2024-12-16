import sys
import unittest

sys.path.append(".")


from app.repositories.models.custom_bot import (
    AgentModel,
    AgentToolModel,
    BedrockGuardrailsModel,
    BedrockKnowledgeBaseModel,
    BotAliasModel,
    BotModel,
    ConversationQuickStarterModel,
    GenerationParamsModel,
    KnowledgeModel,
)
from app.routes.schemas.bot import type_sync_status


def _create_test_bot_model(
    id,
    title,
    description,
    instruction,
    shared_scope,
    shared_status,
    is_starred,
    owner_user_id,
    allowed_cognito_users=[],
    allowed_cognito_groups=[],
    last_used_time=1627984879.9,
    conversation_quick_starters=None,
    bedrock_knowledge_base=None,
    bedrock_guardrails=None,
    sync_status="RUNNING",
    display_retrieved_chunks=True,
    published_api_stack_name=None,
    published_api_datetime=None,
    published_api_codebuild_id=None,
):
    return BotModel(
        id=id,
        title=title,
        description=description,
        instruction=instruction,
        create_time=1627984879.9,
        last_used_time=last_used_time,
        shared_scope=shared_scope,
        shared_status=shared_status,
        allowed_cognito_users=allowed_cognito_users,
        allowed_cognito_groups=allowed_cognito_groups,
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        generation_params=GenerationParamsModel(
            max_tokens=2000,
            top_k=250,
            top_p=0.999,
            temperature=0.6,
            stop_sequences=["Human: ", "Assistant: "],
        ),
        agent=AgentModel(
            tools=[
                AgentToolModel(name="tool1", description="tool1 description"),
                AgentToolModel(name="tool2", description="tool2 description"),
            ]
        ),
        knowledge=KnowledgeModel(
            source_urls=["https://aws.amazon.com/"],
            sitemap_urls=["https://aws.amazon.sitemap.xml"],
            filenames=["test.txt"],
            s3_urls=["s3://test-user/test-bot/"],
        ),
        sync_status=sync_status,
        sync_status_reason="reason",
        sync_last_exec_id="",
        published_api_stack_name=published_api_stack_name,
        published_api_datetime=published_api_datetime,
        published_api_codebuild_id=published_api_codebuild_id,
        display_retrieved_chunks=display_retrieved_chunks,
        conversation_quick_starters=(
            [] if conversation_quick_starters is None else conversation_quick_starters
        ),
        bedrock_knowledge_base=bedrock_knowledge_base,
        bedrock_guardrails=bedrock_guardrails,
    )


def create_test_private_bot(id, is_starred, owner_user_id, **kwargs):
    return _create_test_bot_model(
        id=id,
        title="Test Bot",
        description="Test Bot Description",
        instruction=kwargs.get("instruction", "Test Bot Prompt"),
        shared_scope="private",
        shared_status="unshared",
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        **kwargs,
    )


def create_test_public_bot(id, is_starred, owner_user_id, **kwargs):
    return _create_test_bot_model(
        id=id,
        title="Test Public Bot",
        description="Test Public Bot Description",
        instruction=kwargs.get("instruction", "Test Public Bot Prompt"),
        shared_scope="all",
        shared_status="shared",
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        **kwargs,
    )


def create_test_partial_shared_bot(id, is_starred, owner_user_id, **kwargs):
    return _create_test_bot_model(
        id=id,
        title="Test Partial Shared Bot",
        description="Test Partial Shared Bot Description",
        instruction=kwargs.get("instruction", "Test Partial Shared Bot Prompt"),
        shared_scope="partial",
        shared_status="shared",
        allowed_cognito_users=["user1"],
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        **kwargs,
    )


def create_test_pinned_public_bot(id, is_starred, owner_user_id, **kwargs):
    return _create_test_bot_model(
        id=id,
        title="Test Pinned Bot",
        description="Test Pinned Bot Description",
        instruction=kwargs.get("instruction", "Test Pinned Bot Prompt"),
        shared_scope="all",
        shared_status="pinned@001",
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        **kwargs,
    )


def create_test_pinned_partial_share_bot(id, is_starred, owner_user_id, **kwargs):
    return _create_test_bot_model(
        id=id,
        title="Test Pinned Partial Share Bot",
        description="Test Pinned Partial Share Bot Description",
        instruction=kwargs.get("instruction", "Test Pinned Partial Share Bot Prompt"),
        shared_scope="partial",
        shared_status="pinned@001",
        allowed_cognito_users=["user1"],
        is_starred=is_starred,
        owner_user_id=owner_user_id,
        **kwargs,
    )
