import sys
import unittest

sys.path.append(".")

from app.agents.tools.internet_search import internet_search_tool
from app.repositories.models.custom_bot import (
    ActiveModelsModel,
    AgentModel,
    AgentToolModel,
    BotModel,
    ConversationQuickStarterModel,
    GenerationParamsModel,
    KnowledgeModel,
)
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.repositories.models.custom_bot_kb import (
    BedrockKnowledgeBaseModel,
    OpenSearchParamsModel,
    SearchParamsModel,
    WebCrawlingFiltersModel,
)


class TestBotModel(unittest.TestCase):
    def setUp(self) -> None:
        # Setup fully configured BotModel
        self.bot = BotModel(
            id="test",
            title="test",
            description="test",
            instruction="instruction",
            create_time=1627984879.9,
            last_used_time=1627984879.9,
            shared_scope="all",
            shared_status="shared",
            allowed_cognito_users=["test_user2"],
            allowed_cognito_groups=["test_group1"],
            is_starred=False,
            owner_user_id="test_user1",
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
            published_api_stack_name="published_api_stack_name",
            published_api_datetime=1627984879,
            published_api_codebuild_id="published_api_codebuild_id",
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
        )

    def test_to_output(self):
        # Test to ensure 422 not raised
        output = self.bot.to_output()


if __name__ == "__main__":
    unittest.main()
