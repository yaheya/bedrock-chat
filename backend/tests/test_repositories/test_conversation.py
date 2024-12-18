import base64
import sys
import unittest

sys.path.append(".")


from app.repositories.conversation import (
    ConversationModel,
    MessageModel,
    RecordNotFoundError,
    change_conversation_title,
    delete_conversation_by_id,
    delete_conversation_by_user_id,
    find_conversation_by_id,
    find_conversation_by_user_id,
    store_conversation,
    update_feedback,
)
from app.repositories.custom_bot import (
    delete_bot_by_id,
    find_owned_bots_by_user_id,
    store_bot,
)
from app.repositories.models.conversation import (
    ChunkModel,
    FeedbackModel,
    ImageContentModel,
    SimpleMessageModel,
    TextContentModel,
    ToolUseContentModel,
    ToolUseContentModelBody,
)


class TestConversationRepository(unittest.TestCase):
    def test_store_and_find_conversation(self):
        conversation = ConversationModel(
            id="1",
            create_time=1627984879.9,
            title="Test Conversation",
            total_price=100,
            message_map={
                "a": MessageModel(
                    role="user",
                    content=[
                        TextContentModel(
                            content_type="text",
                            body="Hello",
                        ),
                        ImageContentModel(
                            content_type="image",
                            body=base64.b64decode(
                                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                            ),
                            media_type="image/png",
                        ),
                    ],
                    model="claude-instant-v1",
                    children=["x", "y"],
                    parent="z",
                    create_time=1627984879.9,
                    feedback=None,
                    used_chunks=[
                        ChunkModel(
                            content="chunk1",
                            source="source1",
                            rank=1,
                            content_type="url",
                        ),
                    ],
                    thinking_log=[
                        SimpleMessageModel(
                            role="agent",
                            content=[
                                ToolUseContentModel(
                                    content_type="toolUse",
                                    body=ToolUseContentModelBody(
                                        tool_use_id="xyz1234",
                                        name="internet_search",
                                        input={
                                            "query": "Google news",
                                            "country": "us-en",
                                            "time_limit": "d",
                                        },
                                    ),
                                )
                            ],
                        )
                    ],
                )
            },
            last_message_id="x",
            bot_id=None,
            should_continue=False,
        )

        # Test storing conversation
        response = store_conversation("user", conversation)
        self.assertIsNotNone(response)

        # Test finding conversation by user_id
        conversations = find_conversation_by_user_id(user_id="user")
        self.assertEqual(len(conversations), 1)

        # Test finding conversation by id
        found_conversation = find_conversation_by_id(user_id="user", conversation_id="1")
        self.assertEqual(found_conversation.id, "1")
        message_map = found_conversation.message_map
        # Assert whether the message map is correctly reconstructed
        self.assertEqual(message_map["a"].role, "user")
        content = message_map["a"].content
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0].content_type, "text")
        self.assertEqual(content[0].body, "Hello")
        self.assertEqual(content[1].content_type, "image")
        self.assertEqual(
            content[1].body,
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
        )
        self.assertEqual(message_map["a"].model, "claude-instant-v1")
        self.assertEqual(message_map["a"].children, ["x", "y"])
        self.assertEqual(message_map["a"].parent, "z")
        self.assertEqual(message_map["a"].create_time, 1627984879.9)
        self.assertEqual(len(message_map["a"].used_chunks), 1)  # type: ignore
        self.assertEqual(found_conversation.last_message_id, "x")
        self.assertEqual(found_conversation.total_price, 100)
        self.assertEqual(found_conversation.bot_id, None)
        self.assertEqual(found_conversation.should_continue, False)

        # Agent thinking log
        assert message_map["a"].thinking_log is not None
        self.assertEqual(message_map["a"].thinking_log[0].role, "agent")
        self.assertEqual(
            message_map["a"].thinking_log[0].content[0].content_type, "toolUse"
        )
        self.assertEqual(
            message_map["a"].thinking_log[0].content[0].body.name, "internet_search"  # type: ignore
        )
        self.assertEqual(
            message_map["a"].thinking_log[0].content[0].body.input["query"], "Google news"  # type: ignore
        )

        # Test update title
        response = change_conversation_title(
            user_id="user",
            conversation_id="1",
            new_title="Updated title",
        )
        found_conversation = find_conversation_by_id(user_id="user", conversation_id="1")
        self.assertEqual(found_conversation.title, "Updated title")

        # Test give a feedback
        self.assertIsNone(found_conversation.message_map["a"].feedback)
        response = update_feedback(
            user_id="user",
            conversation_id="1",
            message_id="a",
            feedback=FeedbackModel(
                thumbs_up=True, category="Good", comment="The response is pretty good."
            ),
        )
        found_conversation = find_conversation_by_id(user_id="user", conversation_id="1")
        feedback = found_conversation.message_map["a"].feedback
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.thumbs_up, True)  # type: ignore
        self.assertEqual(feedback.category, "Good")  # type: ignore
        self.assertEqual(feedback.comment, "The response is pretty good.")  # type: ignore

        # Test deleting conversation by id
        delete_conversation_by_id(user_id="user", conversation_id="1")
        with self.assertRaises(RecordNotFoundError):
            find_conversation_by_id("user", "1")

        response = store_conversation(user_id="user", conversation=conversation)

        # Test deleting conversation by user_id
        delete_conversation_by_user_id(user_id="user")
        conversations = find_conversation_by_user_id(user_id="user")
        self.assertEqual(len(conversations), 0)

    def test_store_and_find_large_conversation(self):
        large_message_map = {
            f"msg_{i}": MessageModel(
                role="user",
                content=[
                    TextContentModel(
                        content_type="text",
                        body="This is a large message."
                        * 1000,  # Repeating to make it large
                    )
                ],
                model="claude-instant-v1",
                children=[],
                parent=None,
                create_time=1627984879.9,
                feedback=None,
                used_chunks=None,
                thinking_log=None,
            )
            for i in range(10)  # Create 10 large messages
        }

        large_conversation = ConversationModel(
            id="2",
            create_time=1627984879.9,
            title="Large Conversation",
            total_price=200,
            message_map=large_message_map,
            last_message_id="msg_9",
            bot_id=None,
            should_continue=False,
        )

        # Test storing large conversation with a small threshold
        response = store_conversation("user", large_conversation, threshold=1)
        self.assertIsNotNone(response)

        # Test finding large conversation by id
        found_conversation = find_conversation_by_id(user_id="user", conversation_id="2")
        self.assertEqual(found_conversation.id, "2")
        self.assertEqual(found_conversation.title, "Large Conversation")
        self.assertEqual(found_conversation.total_price, 200)
        self.assertEqual(found_conversation.last_message_id, "msg_9")
        self.assertEqual(found_conversation.bot_id, None)
        self.assertEqual(found_conversation.should_continue, False)

        message_map = found_conversation.message_map
        self.assertEqual(len(message_map), 10)

        for i in range(10):
            message_id = f"msg_{i}"
            self.assertIn(message_id, message_map)
            message = message_map[message_id]
            self.assertEqual(message.role, "user")
            self.assertEqual(len(message.content), 1)
            self.assertEqual(message.content[0].content_type, "text")
            self.assertEqual(message.content[0].body, "This is a large message." * 1000)
            self.assertEqual(message.model, "claude-instant-v1")
            self.assertEqual(message.children, [])
            self.assertEqual(message.parent, None)
            self.assertEqual(message.create_time, 1627984879.9)

        # Test deleting large conversation
        delete_conversation_by_id(user_id="user", conversation_id="2")
        with self.assertRaises(RecordNotFoundError):
            find_conversation_by_id("user", "2")

        store_conversation(user_id="user", conversation=large_conversation)
        delete_conversation_by_user_id(user_id="user")
        conversations = find_conversation_by_user_id(user_id="user")
        self.assertEqual(len(conversations), 0)


if __name__ == "__main__":
    unittest.main()
