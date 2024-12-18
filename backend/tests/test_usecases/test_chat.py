import sys

from ulid import ULID

sys.path.insert(0, ".")
import unittest
from pprint import pprint

import boto3
from app.agents.tools.agent_tool import ToolRunResult
from app.prompt import build_rag_prompt
from app.repositories.conversation import (
    delete_conversation_by_id,
    delete_conversation_by_user_id,
    find_conversation_by_id,
    store_conversation,
)
from app.repositories.custom_bot import (
    delete_alias_by_id,
    delete_bot_by_id,
    store_alias,
    store_bot,
    update_bot_shared_status,
)
from app.repositories.models.conversation import (
    ConversationModel,
    MessageModel,
    TextContentModel,
)
from app.repositories.models.custom_bot import BotAliasModel
from app.repositories.models.custom_bot_guardrails import BedrockGuardrailsModel
from app.routes.schemas.conversation import (
    AttachmentContent,
    ChatInput,
    ImageContent,
    MessageInput,
    TextContent,
    type_model_name,
)
from app.stream import OnStopInput, OnThinking
from app.usecases.chat import (
    chat,
    chat_output_from_message,
    fetch_conversation,
    propose_conversation_title,
    trace_to_root,
)
from app.vector_search import SearchResult
from tests.test_repositories.utils.bot_factory import (
    create_test_private_bot,
    create_test_public_bot,
)
from tests.test_stream.get_aws_logo import get_aws_logo
from tests.test_stream.get_pdf import get_aws_overview
from tests.test_usecases.utils.user_factory import (
    create_test_admin_user,
    create_test_user,
)

MODEL: type_model_name = "claude-v3-haiku"
MISTRAL_MODEL: type_model_name = "mistral-7b-instruct"


class TestTraceToRoot(unittest.TestCase):
    def test_trace_to_root(self):
        message_map = {
            "user_1": MessageModel(
                role="user",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="user_1",
                    )
                ],
                model=MODEL,
                children=["bot_1"],
                parent=None,
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
            "bot_1": MessageModel(
                role="assistant",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="bot_1",
                    )
                ],
                model=MODEL,
                children=["user_2"],
                parent="user_1",
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
            "user_2": MessageModel(
                role="user",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="user_2",
                    )
                ],
                model=MODEL,
                children=["bot_2"],
                parent="bot_1",
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
            "bot_2": MessageModel(
                role="assistant",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="bot_2",
                    )
                ],
                model=MODEL,
                children=["user_3a", "user_3b"],
                parent="user_2",
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
            "user_3a": MessageModel(
                role="user",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="user_3a",
                    )
                ],
                model=MODEL,
                children=[],
                parent="bot_2",
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
            "user_3b": MessageModel(
                role="user",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="user_3b",
                    )
                ],
                model=MODEL,
                children=[],
                parent="bot_2",
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            ),
        }
        messages = trace_to_root("user_3a", message_map)
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].content[0].body, "user_1")
        self.assertEqual(messages[1].content[0].body, "bot_1")
        self.assertEqual(messages[2].content[0].body, "user_2")
        self.assertEqual(messages[3].content[0].body, "bot_2")
        self.assertEqual(messages[4].content[0].body, "user_3a")

        messages = trace_to_root("user_3b", message_map)
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].content[0].body, "user_1")
        self.assertEqual(messages[1].content[0].body, "bot_1")
        self.assertEqual(messages[2].content[0].body, "user_2")
        self.assertEqual(messages[3].content[0].body, "bot_2")
        self.assertEqual(messages[4].content[0].body, "user_3b")


class TestStartChat(unittest.TestCase):
    user = create_test_user("user1")

    def test_chat(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="あなたの名前は何ですか？",
                    )
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        self.output = output

        pprint(output.model_dump())

        self.assertNotEqual(output.conversation_id, "")

        conv = find_conversation_by_id(
            user_id="user1", conversation_id=output.conversation_id
        )
        # Message length will be 2 (system + user input + assistant reply)
        self.assertEqual(len(conv.message_map), 3)
        for k, v in conv.message_map.items():
            if v.parent == "system":
                first_key = k
                first_message = v
            elif v.parent:
                second_key = k
                second_message = v

        self.assertEqual(second_message.parent, first_key)
        self.assertEqual(first_message.children, [second_key])
        self.assertEqual(conv.last_message_id, second_key)
        self.assertNotEqual(conv.total_price, 0)

    # def test_chat_mistral(self):
    #     prompt = "あなたの名前は何ですか?"
    #     body = f"<s>[INST]{prompt}[/INST]"

    #     chat_input = ChatInput(
    #         conversation_id="test_conversation_id",
    #         message=MessageInput(
    #             role="user",
    #             content=[
    #                 TextContent(
    #                     content_type="text",
    #                     body=body,
    #                 )
    #             ],
    #             model=MISTRAL_MODEL,
    #             parent_message_id=None,
    #             message_id=None,
    #         ),
    #         bot_id=None,
    #         continue_generate=False,
    #     )
    #     conversation, message = chat(user_id="user1", chat_input=chat_input)
    #     output = chat_output_from_message(conversation=conversation, message=message)
    #     self.output = output

    #     pprint(output.model_dump())
    #     self.assertNotEqual(output.conversation_id, "")

    #     conv = find_conversation_by_id(
    #         user_id="user1", conversation_id=output.conversation_id
    #     )
    #     self.assertEqual(len(conv.message_map), 3)
    #     for k, v in conv.message_map.items():
    #         if v.parent == "system":
    #             first_key = k
    #             first_message = v
    #         elif v.parent:
    #             second_key = k
    #             second_message = v

    #     self.assertEqual(second_message.parent, first_key)
    #     self.assertEqual(first_message.children, [second_key])
    #     self.assertEqual(conv.last_message_id, second_key)
    #     self.assertNotEqual(conv.total_price, 0)

    def tearDown(self) -> None:
        delete_conversation_by_id("user1", self.output.conversation_id)


class TestAttachmentChat(unittest.TestCase):
    user = create_test_user("user1")

    def tearDown(self) -> None:
        delete_conversation_by_id("user1", self.output.conversation_id)

    def test_chat(self):
        file_name, body = get_aws_overview()

        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    AttachmentContent(
                        content_type="attachment",
                        body=body,
                        file_name=file_name,
                    ),
                    TextContent(
                        content_type="text",
                        body="Summarize the document.",
                    ),
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        pprint(output.model_dump())
        self.output = output


class TestMultimodalChat(unittest.TestCase):
    user = create_test_user("user1")

    def tearDown(self) -> None:
        delete_conversation_by_id("user1", self.output.conversation_id)

    def test_chat(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    ImageContent(
                        content_type="image",
                        # AWS Logo image
                        body=get_aws_logo(),
                        media_type="image/png",
                    ),
                    TextContent(
                        content_type="text",
                        body="Explain the image",
                    ),
                ],
                model="claude-v3-sonnet",  # Specify v3 model
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        message = MessageModel.from_message_input(chat_input.message)
        print(message.content[0].body)
        print(type(message.content[0].body))

        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        # Check the output whether the explanation is about aws logo
        pprint(output.model_dump())
        self.output = output


class TestContinueChat(unittest.TestCase):
    user = create_test_user("user1")

    def setUp(self) -> None:
        self.conversation_id = "conversation2"
        store_conversation(
            user_id=self.user.id,
            conversation=ConversationModel(
                last_message_id="b-2",
                id=self.conversation_id,
                create_time=1627984879.9,
                title="Test Conversation",
                total_price=0,
                message_map={
                    "1-user": MessageModel(
                        role="user",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="こんにちは",
                            )
                        ],
                        model=MODEL,
                        children=["1-assistant"],
                        parent=None,
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                    "1-assistant": MessageModel(
                        role="assistant",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="はい、こんにちは。どうしましたか?",
                            )
                        ],
                        model=MODEL,
                        children=[],
                        parent="1-user",
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                },
                bot_id=None,
                should_continue=False,
            ),
        )

    def test_continue_chat(self):
        chat_input = ChatInput(
            conversation_id=self.conversation_id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="あなたの名前は？",
                    )
                ],
                model=MODEL,
                parent_message_id="1-assistant",
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        self.output = output

        pprint(output.model_dump())

        conv = find_conversation_by_id(self.user.id, output.conversation_id)

        messages = trace_to_root(conv.last_message_id, conv.message_map)
        self.assertEqual(len(messages), 4)

        num_empty_children = 0
        for k, v in conv.message_map.items():
            if len(v.children) == 0:
                num_empty_children += 1
        self.assertEqual(num_empty_children, 1)

    def tearDown(self) -> None:
        delete_conversation_by_id(self.user.id, self.output.conversation_id)


class TestRegenerateChat(unittest.TestCase):
    user = create_test_user("user1")

    def setUp(self) -> None:
        self.conversation_id = "conversation3"
        store_conversation(
            user_id=self.user.id,
            conversation=ConversationModel(
                last_message_id="b-2",
                id=self.conversation_id,
                create_time=1627984879.9,
                title="Test Conversation",
                total_price=0,
                message_map={
                    "a-1": MessageModel(
                        role="user",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="こんにちはを英語で",
                            )
                        ],
                        model=MODEL,
                        children=["a-2"],
                        parent=None,
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                    "a-2": MessageModel(
                        role="assistant",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="Hello!",
                            )
                        ],
                        model=MODEL,
                        children=[],
                        parent="a-1",
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                    "b-1": MessageModel(
                        role="user",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="こんにちはを中国語で",
                            )
                        ],
                        model=MODEL,
                        children=["b-2"],
                        parent=None,
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                    "b-2": MessageModel(
                        role="assistant",
                        content=[
                            TextContentModel(
                                content_type="text",
                                body="你好!",
                            )
                        ],
                        model=MODEL,
                        children=[],
                        parent="b-1",
                        create_time=1627984879.9,
                        feedback=None,
                        used_chunks=None,
                        thinking_log=None,
                    ),
                },
                bot_id=None,
                should_continue=False,
            ),
        )

    def test_chat(self):
        # Question for English
        chat_input = ChatInput(
            conversation_id=self.conversation_id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="では、おやすみなさいはなんと言う？",
                    )
                ],
                model=MODEL,
                # a-2: en, b-2: zh
                parent_message_id="a-2",
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        self.output = output

        pprint(output.model_dump())  # English
        conv = find_conversation_by_id(self.user.id, output.conversation_id)
        self.assertEqual(len(conv.message_map), 6)

        # Question for Chinese
        chat_input = ChatInput(
            conversation_id=self.conversation_id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="では、おやすみなさいはなんと言う？",
                    )
                ],
                model=MODEL,
                # a-2: en, b-2: zh
                parent_message_id="b-2",
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        self.output = output

        pprint(output.model_dump())  # Chinese
        conv = find_conversation_by_id(self.user.id, output.conversation_id)
        self.assertEqual(len(conv.message_map), 8)

    def tearDown(self) -> None:
        delete_conversation_by_id(self.user.id, self.conversation_id)


class TestProposeTitle(unittest.TestCase):
    user = create_test_user("user1")

    def setUp(self) -> None:
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        # body="Australian famous site seeing place",
                        body="日本の有名な料理を3つ教えて",
                    )
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=None,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output)
        self.output = output

        # chat_input.conversation_id = "test_conversation_mistral_id"
        # chat_input.message.model = MISTRAL_MODEL
        # conversation, message = chat(user_id="user1", chat_input=chat_input)
        # mistral_output = chat_output_from_message(conversation=conversation, message=message)
        # self.mistral_output = mistral_output
        # print(mistral_output)

    def test_propose_title(self):
        title = propose_conversation_title(self.user.id, self.output.conversation_id)
        print(f"[title]: {title}")

    # def test_propose_title_mistral(self):
    #     title = propose_conversation_title("user1", self.mistral_output.conversation_id)
    #     print(f"[title]: {title}")

    def tearDown(self) -> None:
        delete_conversation_by_id(self.user.id, self.output.conversation_id)


class TestChatWithCustomizedBot(unittest.TestCase):
    first_user = create_test_user("user1")
    second_user = create_test_user("user2")

    first_private_bot_id = "private1"
    first_public_bot_id = "public1"

    def setUp(self) -> None:
        private_bot = create_test_private_bot(
            self.first_private_bot_id,
            True,
            self.first_user.id,
            instruction="俺様風の口調で",
        )
        public_bot = create_test_public_bot(
            self.first_public_bot_id,
            True,
            self.second_user.id,
            instruction="大阪弁で",
        )
        store_bot(private_bot)
        store_bot(public_bot)

        store_alias(
            self.first_user.id, BotAliasModel.from_bot_for_initial_alias(public_bot)
        )

    def tearDown(self) -> None:
        delete_bot_by_id(self.first_user.id, self.first_private_bot_id)
        delete_bot_by_id(self.second_user.id, self.first_public_bot_id)
        delete_conversation_by_user_id(self.first_user.id)

    def test_chat_with_private_bot(self):
        # First message
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="こんにちは",
                    )
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id="private1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output)

        conv = find_conversation_by_id("user1", output.conversation_id)
        self.assertEqual(len(conv.message_map["system"].children), 1)
        self.assertEqual(conv.message_map["system"].children, ["instruction"])
        self.assertEqual(len(conv.message_map["instruction"].children), 1)

        # Second message
        chat_input = ChatInput(
            conversation_id=conv.id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="自己紹介して",
                    )
                ],
                model=MODEL,
                parent_message_id=conv.last_message_id,
                message_id=None,
            ),
            bot_id="private1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output)

        # Edit first message
        chat_input = ChatInput(
            conversation_id=conv.id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="こんばんは",
                    )
                ],
                model=MODEL,
                parent_message_id="system",
                message_id=None,
            ),
            bot_id="private1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)

        conv = find_conversation_by_id("user1", output.conversation_id)
        self.assertEqual(len(conv.message_map["system"].children), 1)
        self.assertEqual(conv.message_map["system"].children[0], "instruction")
        self.assertEqual(len(conv.message_map["instruction"].children), 2)

    def test_chat_with_public_bot(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="こんにちは",
                    )
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id="public1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)

        print(output)

        conv = find_conversation_by_id("user1", output.conversation_id)
        chat_input = ChatInput(
            conversation_id=conv.id,
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="自己紹介して",
                    )
                ],
                model=MODEL,
                parent_message_id=conv.last_message_id,
                message_id=None,
            ),
            bot_id="private1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output)

        # Delete alias
        delete_alias_by_id("user1", "public1")

    def test_fetch_conversation(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="君の名は？",
                    )
                ],
                model=MODEL,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id="private1",
            continue_generate=False,
        )
        conversation, message = chat(self.first_user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)

        conv = fetch_conversation("user1", output.conversation_id)
        # Assert that instruction is not included
        self.assertIsNone(conv.message_map.get("instruction"))


def on_thinking(to_send: OnThinking):
    print("====================================")
    print("Thinking...")
    print("====================================")
    pprint(to_send)


def on_tool_result(run_result: ToolRunResult):
    print("====================================")
    print("Tool Result...")
    print("====================================")
    pprint(run_result)


def on_stop(on_stop_input: OnStopInput):
    print("====================================")
    print("Stop...")
    print("====================================")
    pprint(on_stop_input)


class TestAgentChat(unittest.TestCase):
    user = create_test_user("user1")
    bot_id = "bot1"
    model: type_model_name = "claude-v3-sonnet"

    def setUp(self) -> None:
        private_bot = create_test_private_bot(
            self.bot_id,
            True,
            self.user.id,
            include_internet_tool=True,
        )
        store_bot(private_bot)

    def tearDown(self) -> None:
        delete_bot_by_id(self.user.id, self.bot_id)
        delete_conversation_by_user_id(self.user.id)

    def test_agent_chat(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        body="Today's amazon stock price?",
                    )
                ],
                model=self.model,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=self.bot_id,
            continue_generate=False,
        )
        conversation, message = chat(
            self.user,
            chat_input=chat_input,
            on_thinking=on_thinking,
            on_tool_result=on_tool_result,
            on_stop=on_stop,
        )
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output.message.content[0].body)

        conv = find_conversation_by_id(self.user.id, output.conversation_id)
        # Assert if thinking log is not empty
        assistant_message = conv.message_map[conv.last_message_id]
        self.assertIsNotNone(assistant_message.thinking_log)
        print("Thinking log: ", assistant_message.thinking_log)


class TestGuardrailChat(unittest.TestCase):
    user = create_test_user("user1")
    bot_id = "bot1"
    model: type_model_name = "claude-v3-sonnet"

    def setUp(self) -> None:

        # Note that the region must be the same as the one used in the bedrock client
        # https://github.com/aws/aws-sdk-js-v3/issues/6482
        self.bedrock_client = boto3.client("bedrock", region_name="us-east-1")
        self.guardrail_name = f"test-guardrail-{ULID()}"

        # Create dummy guardrail
        res = self.bedrock_client.create_guardrail(
            name=self.guardrail_name,
            description="Test guardrail for unit tests",
            contentPolicyConfig={
                "filtersConfig": [
                    {
                        "type": "SEXUAL",
                        "inputStrength": "HIGH",
                        "outputStrength": "HIGH",
                    },
                ]
            },
            blockedInputMessaging="blocked",
            blockedOutputsMessaging="blocked",
        )
        self.guardrail_arn = res["guardrailArn"]

        private_bot = create_test_private_bot(
            self.bot_id,
            True,
            self.user.id,
            include_internet_tool=False,
            bedrock_guardrails=BedrockGuardrailsModel(
                is_guardrail_enabled=True,
                hate_threshold=0,
                insults_threshold=0,
                sexual_threshold=1,
                violence_threshold=0,
                misconduct_threshold=0,
                grounding_threshold=0,
                relevance_threshold=0,
                guardrail_arn=res["guardrailArn"],
                guardrail_version="DRAFT",
            ),
        )
        store_bot(private_bot)

    def tearDown(self) -> None:
        delete_bot_by_id(self.user.id, self.bot_id)
        delete_conversation_by_user_id(self.user.id)
        # Delete dummy guardrail
        try:
            self.bedrock_client.delete_guardrail(guardrailIdentifier=self.guardrail_arn)

        except Exception as e:
            print(f"Error deleting guardrail: {e}")

    def test_guardrail_chat(self):
        chat_input = ChatInput(
            conversation_id="test_conversation_id",
            message=MessageInput(
                role="user",
                content=[
                    TextContent(
                        content_type="text",
                        # Sexual content
                        body="Which bust do you like, A cup, B cup, C cup, D cup, or E cup?",
                    )
                ],
                model=self.model,
                parent_message_id=None,
                message_id=None,
            ),
            bot_id=self.bot_id,
            continue_generate=False,
        )
        conversation, message = chat(self.user, chat_input=chat_input)
        output = chat_output_from_message(conversation=conversation, message=message)
        print(output.message.content[0].body)

        # Must be blocked
        assert output.message.content[0].body == "blocked"


class TestInsertKnowledge(unittest.TestCase):
    def test_insert_knowledge(self):
        results: list[SearchResult] = [
            {
                "bot_id": "bot_bb                    ",
                "content": "73\n\nその他リソース\n\nサービス概要: https://aws.amazon.com/jp/opensearch-service/features/serverless/\n\nよくある質問: https://aws.amazon.com/opensearch-service/faqs/#Serverless\n\n料金: https://aws.amazon.com/opensearch-\n\nservice/pricing/?nc1=h_ls#Amazon_OpenSearch_Serverless\n\nドキュメント: https://docs.aws.amazon.com/opensearch- service/latest/developerguide/serverless.html\n\nOpenSearch Service と OpenSearch Serverless の比較:\n\nhttps://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless- overview.html#serverless-comparison\n\nワークショップ: https://catalog.us-east-1.prod.workshops.aws/workshops/f8d2c175- 634d-4c5d-94cb-d83bbc656c6a\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\n74\n\n本資料に関するお問い合わせ・ご感想\n\n技術的な内容に関しましては、有料のAWSサポート窓口へ お問い合わせください\n\nhttps://aws.amazon.com/jp/premiumsupport/\n\n料金面でのお問い合わせに関しましては、カスタマーサポート窓口へ お問い合わせください（マネジメントコンソールへのログインが必要です）\n\nhttps://console.aws.amazon.com/support/home#/case/create?issueType=customer- service\n\n具体的な案件に対する構成相談は、後述する個別相談会をご活用ください",
                "source_name": "AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "source_link": "https://pages.awscloud.com/rs/112-TZM-766/images/AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "rank": 0,
            },
            {
                "bot_id": "bot_bb                    ",
                "content": "70\n\nAmazon OpenSearch Serverless がフィットするケース\n\n事前のキャパシティプランニングが困難\n\n一日の間で負荷の変動が激しい\n\n一般的な検索アプリケーション、もしくは小規模 (TiB オーダー) のログ分析が想定用途\n\nノードやクラスターのスケール、セキュリティパッチ適用といった 運用タスクをなるべく削減したい\n\nAmazon OpenSearch Serverless 固有の制限 (API、プラグイン) が利用上の問題にならない\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\n71\n\n従来の Amazon OpenSearch Service がフィットするケース\n\n事前にキャパシティプランニングが可能\n\n一日の間で負荷が一定、もしくは増減の予測が可能\n\n数十 TiB オーダーの大規模なデータから分析や検索を行う 必要がある\n\nベクトル検索やアラート、セキュリティ機能など、 OpenSearch の高度な機能を利用する必要がある\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\n72\n\nまとめ\n\nOpenSearch Serverless は OpenSearch 互換のサーバレスサービスである\n\n負荷に応じて OCU が動的に増減する、自動スケールアウト、スケールインを サポートしている\n\n従来アーキテクチャで行っていたアップデートなどの運用タスクを削減できる\n\nOpenSearch Serverless 固有の制限あり (API、プラグイン、その他機能)\n\n従来の Amazon OpenSearch Service からの移行に際しては、 既存のワークロードや要件を確認し、移行の可能性を検討してから行うこと\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\n73\n\nその他リソース\n\nサービス概要: https://aws.amazon.com/jp/opensearch-service/features/serverless/",
                "source_name": "AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "source_link": "https://pages.awscloud.com/rs/112-TZM-766/images/AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "rank": 1,
            },
            {
                "bot_id": "bot_bb                    ",
                "content": "67\n\n料金\n\nポイント • OpenSearch Serverless の料金モデルは、\n\n割り当てられたキャパシティユニットに応じた時間課金\n\n料金概要(東京リージョン) • OCU – インデキシング : $0.334 per OCU per hour • OCU – 検索: $0.334 per OCU per hour • マネージドストレージ: $0.026 per GB / month • OpenSearch Dashboards は無料で利用可能\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\nhttps://aws.amazon.com/jp/opensearch-service/pricing/#Amazon_OpenSearch_Serverless\n\n68\n\n主要な制限\n\nアカウント(リージョン)毎の制限 • インデックス可能なデータサイズ : 6 TiB\n\n(超過分のデータはノード上のディスクではなく S3 に格納)\n\nコレクション数: 50 • 検索用 OCU: 50 • インデキシング用 OCU: 50\n\nコレクションごとの制限 • インデックス可能なデータサイズ : 1 TiB\n\n(超過分のデータはノード上のディスクではなく S3 に格納)\n\nインデックス数(検索コレクション): 20 • インデックス数(時系列コレクション): 120\n\n© 2023, Amazon Web Services, Inc. or its affiliates.\n\nhttps://docs.aws.amazon.com/opensearch-service/latest/developerguide/limits.html#limits-serverless\n\n69\n\nまとめ\n\n© 2023, Amazon Web Services, Inc. or its affiliates. © 2023, Amazon Web Services, Inc. or its affiliates.\n\n70\n\nAmazon OpenSearch Serverless がフィットするケース\n\n事前のキャパシティプランニングが困難\n\n一日の間で負荷の変動が激しい",
                "source_name": "AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "source_link": "https://pages.awscloud.com/rs/112-TZM-766/images/AWS-Black-Belt_2023_AmazonOpenSearchServerless_0131_v1.pdf",
                "rank": 2,
            },
        ]
        instruction = build_rag_prompt(
            search_results=results,
            display_citation=True,
        )
        print(instruction)


if __name__ == "__main__":
    unittest.main()
