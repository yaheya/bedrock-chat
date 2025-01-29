import sys
import unittest

sys.path.insert(0, ".")

import time

from app.agents.tools.internet_search import internet_search_tool
from app.repositories.models.custom_bot import (
    ActiveModelsModel,
    AgentModel,
    AgentToolModel,
    BotModel,
    ConversationQuickStarterModel,
    GenerationParamsModel,
    KnowledgeModel,
    UsageStatsModel,
)
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.repositories.models.custom_bot_kb import (
    BedrockKnowledgeBaseModel,
    OpenSearchParamsModel,
    SearchParamsModel,
    WebCrawlingFiltersModel,
)
from tests.test_usecases.utils.user_factory import (
    create_test_user,
    delete_cognito_group,
    delete_cognito_user,
    store_group_in_cognito,
    store_user_in_cognito,
)


class TestBotModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.group_name = "test_group"
        store_group_in_cognito(cls.group_name)

        # Wait for reflecting the changes in the user pool
        time.sleep(3)

        cls.owner = create_test_user("test_owner")
        store_user_in_cognito(cls.owner)
        cls.user = create_test_user("test_user")
        store_user_in_cognito(cls.user)
        cls.user_in_group = create_test_user(
            "test_user_in_group", groups=[cls.group_name]
        )
        store_user_in_cognito(cls.user_in_group)

        # Wait for reflecting the changes in the user pool
        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        delete_cognito_user(cls.owner)
        delete_cognito_user(cls.user)
        delete_cognito_user(cls.user_in_group)
        delete_cognito_group(cls.group_name)

    def setUp(self) -> None:
        # Setup fully configured BotModel
        self.bot = BotModel(
            id="test",
            title="test",
            description="test",
            instruction="instruction",
            create_time=1627984879.9,
            last_used_time=1627984879.9,
            shared_scope="partial",
            shared_status="shared",
            allowed_cognito_users=[],
            allowed_cognito_groups=["test_group"],
            is_starred=False,
            owner_user_id=self.owner.id,
            generation_params=GenerationParamsModel(
                max_tokens=2000,
                top_k=250,
                top_p=0.999,
                temperature=0.6,
                stop_sequences=["Human: ", "Assistant: "],
            ),
            agent=AgentModel(
                tools=(
                    [
                        AgentToolModel(
                            name=internet_search_tool.name,
                            description=internet_search_tool.description,
                        )
                    ]
                ),
            ),
            knowledge=(
                KnowledgeModel(
                    source_urls=["https://aws.amazon.com/"],
                    sitemap_urls=["https://aws.amazon.sitemap.xml"],
                    filenames=["test.txt"],
                    s3_urls=["s3://test-user/test-bot/"],
                )
            ),
            sync_status="RUNNING",
            sync_status_reason="reason",
            sync_last_exec_id="xxxx",
            published_api_stack_name=None,
            published_api_datetime=None,
            published_api_codebuild_id=None,
            display_retrieved_chunks=True,
            conversation_quick_starters=[
                ConversationQuickStarterModel(
                    title="title",
                    example="example",
                )
            ],
            bedrock_knowledge_base=(
                BedrockKnowledgeBaseModel(
                    embeddings_model="titan_v2",
                    open_search=OpenSearchParamsModel(analyzer=None),
                    chunking_configuration=None,
                    search_params=SearchParamsModel(
                        max_results=10, search_type="hybrid"
                    ),
                    knowledge_base_id="test-knowledge-base-id",
                    data_source_ids=["data-source-1", "data-source-2"],
                    parsing_model="disabled",
                    web_crawling_scope="DEFAULT",
                    web_crawling_filters=WebCrawlingFiltersModel(
                        exclude_patterns=["exclude-pattern"],
                        include_patterns=["include-pattern"],
                    ),
                )
            ),
            bedrock_guardrails=BedrockGuardrailsModel(
                is_guardrail_enabled=True,
                hate_threshold=5,
                insults_threshold=5,
                sexual_threshold=5,
                violence_threshold=5,
                misconduct_threshold=5,
                grounding_threshold=0.5,
                relevance_threshold=0.5,
                guardrail_arn="guardrail_arn",
                guardrail_version="guardrail_version",
            ),
            active_models=ActiveModelsModel(
                claude_v3_sonnet_v2=True,
            ),
            usage_stats=UsageStatsModel(usage_count=0),
        )

    def test_to_output(self):
        # Test to ensure 422 not raised
        output = self.bot.to_output()

    def test_is_accessible_by_user(self):
        self.assertTrue(self.bot.is_accessible_by_user(self.owner))
        self.assertFalse(self.bot.is_accessible_by_user(self.user))
        self.assertTrue(self.bot.is_accessible_by_user(self.user_in_group))

    def test_is_editable_by_user(self):
        self.assertTrue(self.bot.is_editable_by_user(self.owner))
        self.assertFalse(self.bot.is_editable_by_user(self.user))
        self.assertFalse(self.bot.is_editable_by_user(self.user_in_group))

    def test_is_owned_by_user(self):
        self.assertTrue(self.bot.is_owned_by_user(self.owner))
        self.assertFalse(self.bot.is_owned_by_user(self.user))
        self.assertFalse(self.bot.is_owned_by_user(self.user_in_group))


if __name__ == "__main__":
    unittest.main()
