import sys

sys.path.insert(0, ".")
import unittest

from app.repositories.custom_bot import (
    delete_alias_by_id,
    delete_bot_by_id,
    find_bot_by_id,
    store_bot,
    update_bot_shared_status,
)
from app.routes.schemas.admin import (
    PushBotInput,
    PushBotInputPinned,
    PushBotInputUnpinned,
)
from app.routes.schemas.bot import (
    AllVisibilityInput,
    BotSwitchVisibilityInput,
    PartialVisibilityInput,
    PrivateVisibilityInput,
)
from app.usecases.bot import (
    fetch_all_bots,
    fetch_all_pinned_bots,
    fetch_bot,
    fetch_bot_summary,
    issue_presigned_url,
    modify_bot_visibility,
    modify_pinning_status,
    modify_star_status,
)
from tests.test_repositories.utils.bot_factory import (
    create_test_partial_shared_bot,
    create_test_pinned_partial_share_bot,
    create_test_pinned_public_bot,
    create_test_private_bot,
    create_test_public_bot,
)
from tests.test_usecases.utils.user_factory import (
    create_test_admin_user,
    create_test_user,
    delete_cognito_user,
    store_user_in_cognito,
)


class TestIssuePresignedUrl(unittest.TestCase):
    def test_issue_presigned_url(self):
        user = create_test_user("test_user")
        url = issue_presigned_url(user, "test_bot", "test_file", content_type="image/png")
        self.assertEqual(type(url), str)
        self.assertTrue(url.startswith("https://"))


class TestModifyBotVisibility(unittest.TestCase):
    user = create_test_user("user1")

    def setUp(self) -> None:
        self.bot = create_test_private_bot(
            id="1", is_starred=False, owner_user_id="user1"
        )
        store_bot(self.bot)

    def tearDown(self) -> None:
        delete_bot_by_id("user1", "1")

    def test_modify_visibility_to_private(self):
        input_data = PrivateVisibilityInput(target_shared_scope="private")

        modify_bot_visibility(self.user, "1", input_data)
        updated_bot = find_bot_by_id("1")

        self.assertEqual(updated_bot.shared_scope, "private")
        self.assertEqual(updated_bot.shared_status, "unshared")
        self.assertEqual(updated_bot.allowed_cognito_users, [])
        self.assertEqual(updated_bot.allowed_cognito_groups, [])

    def test_modify_visibility_to_partial(self):
        input_data = PartialVisibilityInput(
            target_shared_scope="partial",
            target_allowed_user_ids=["user2", "user3"],
            target_allowed_group_ids=["group1"],
        )

        modify_bot_visibility(self.user, "1", input_data)
        updated_bot = find_bot_by_id("1")

        self.assertEqual(updated_bot.shared_scope, "partial")
        self.assertEqual(updated_bot.shared_status, "shared")
        self.assertEqual(updated_bot.allowed_cognito_users, ["user2", "user3"])
        self.assertEqual(updated_bot.allowed_cognito_groups, ["group1"])

    def test_modify_visibility_to_all(self):
        input_data = AllVisibilityInput(target_shared_scope="all")

        modify_bot_visibility(self.user, "1", input_data)
        updated_bot = find_bot_by_id("1")

        self.assertEqual(updated_bot.shared_scope, "all")
        self.assertEqual(updated_bot.shared_status, "shared")
        self.assertEqual(updated_bot.allowed_cognito_users, [])
        self.assertEqual(updated_bot.allowed_cognito_groups, [])

    def test_modify_visibility_permission_denied(self):
        input_data = PrivateVisibilityInput(target_shared_scope="private")
        user = create_test_user("user2")

        with self.assertRaises(PermissionError) as context:
            modify_bot_visibility(user, "1", input_data)

    def test_cannot_modify_visibility_to_pinned_without_permission(self):
        input_data = AllVisibilityInput(target_shared_scope="all")
        user = create_test_user("user2")

        with self.assertRaises(PermissionError) as context:
            modify_bot_visibility(user, "1", input_data)

    def test_can_modify_visibility_by_admin(self):
        input_data = AllVisibilityInput(target_shared_scope="all")
        user = create_test_admin_user("admin")

        modify_bot_visibility(user, "1", input_data)
        updated_bot = find_bot_by_id("1")

        self.assertEqual(updated_bot.shared_scope, "all")
        self.assertEqual(updated_bot.shared_status, "shared")
        self.assertEqual(updated_bot.allowed_cognito_users, [])
        self.assertEqual(updated_bot.allowed_cognito_groups, [])


class TestModifyPinnedBotVisibilityNarrowing(unittest.TestCase):
    user = create_test_user("user1")

    def setUp(self) -> None:
        self.partial_bot = create_test_pinned_partial_share_bot(
            id="1", is_starred=False, owner_user_id="user1"
        )
        self.public_bot = create_test_pinned_public_bot(
            id="2", is_starred=False, owner_user_id="user1"
        )
        store_bot(self.partial_bot)
        store_bot(self.public_bot)

    def tearDown(self) -> None:
        delete_bot_by_id("user1", "1")
        delete_bot_by_id("user1", "2")

    def test_modify_visibility_pinned_bot_scope_narrowing_to_private(self):
        input_data = PrivateVisibilityInput(target_shared_scope="private")

        with self.assertRaises(ValueError) as context:
            modify_bot_visibility(self.user, "1", input_data)

        with self.assertRaises(ValueError) as context:
            modify_bot_visibility(self.user, "2", input_data)

    def test_modify_visibility_pinned_bot_scope_narrowing_to_partial(self):
        input_data = PartialVisibilityInput(
            target_shared_scope="partial",
            target_allowed_user_ids=["user2", "user3"],
            target_allowed_group_ids=["group1"],
        )

        with self.assertRaises(ValueError) as context:
            modify_bot_visibility(self.user, "2", input_data)


class TestModifyPinningStatus(unittest.TestCase):
    def setUp(self) -> None:
        self.public_bot = create_test_public_bot(
            id="1", is_starred=False, owner_user_id="user1"
        )
        store_bot(self.public_bot)

        self.private_bot = create_test_private_bot(
            id="2", is_starred=False, owner_user_id="user1"
        )
        store_bot(self.private_bot)

    def tearDown(self) -> None:
        delete_bot_by_id("user1", "1")
        delete_bot_by_id("user1", "2")

    def test_pinning_status_pinned(self):
        input_data = PushBotInputPinned(to_pinned=True, order=1)
        modify_pinning_status("1", input_data)

        updated_bot = find_bot_by_id("1")
        self.assertEqual(updated_bot.shared_status, "pinned@001")

    def test_pinning_status_unpinned(self):
        input_data = PushBotInputPinned(to_pinned=True, order=1)
        modify_pinning_status("1", input_data)

        input_unpin = PushBotInputUnpinned(to_pinned=False)
        modify_pinning_status("1", input_unpin)

        updated_bot = find_bot_by_id("1")
        self.assertEqual(updated_bot.shared_status, "shared")

    def test_pinning_status_private_bot(self):
        input_data = PushBotInputPinned(to_pinned=True, order=1)

        with self.assertRaises(ValueError) as context:
            modify_pinning_status("2", input_data)

    def test_unpinning_status_private_bot(self):
        input_data = PushBotInputUnpinned(to_pinned=False)

        with self.assertRaises(ValueError) as context:
            modify_pinning_status("2", input_data)


class TestScenario(unittest.TestCase):
    user1 = create_test_user("user1")
    user2 = create_test_user("user2")
    admin = create_test_admin_user("admin")

    @classmethod
    def setUpClass(cls) -> None:
        store_user_in_cognito(cls.user1)
        store_user_in_cognito(cls.user2)
        store_user_in_cognito(cls.admin)

    @classmethod
    def tearDownClass(cls) -> None:
        delete_cognito_user(cls.user1)
        delete_cognito_user(cls.user2)
        delete_cognito_user(cls.admin)

    def setUp(self) -> None:
        # Create user1 bots
        self.user1_bot1 = create_test_private_bot("1", False, "user1")
        self.user1_bot2 = create_test_private_bot("2", False, "user1")

        # Create user2 bots
        self.user2_bot1 = create_test_partial_shared_bot("3", False, "user2", ["user10"])
        self.user2_bot2 = create_test_partial_shared_bot("4", False, "user2", ["user1"])

        store_bot(self.user1_bot1)
        store_bot(self.user1_bot2)
        store_bot(self.user2_bot1)
        store_bot(self.user2_bot2)

    def tearDown(self) -> None:
        delete_bot_by_id("user1", "1")
        delete_bot_by_id("user1", "2")
        delete_bot_by_id("user2", "3")
        delete_bot_by_id("user2", "4")

        try:
            delete_alias_by_id("user1", "3")
        except Exception:
            print("Alias not found")
            pass

        try:
            delete_alias_by_id("user1", "4")
        except Exception:
            print("Alias not found")
            pass

    def test_scenario(self):
        # Step 1: user1がuser2のボットを取得しようとする (失敗)
        with self.assertRaises(PermissionError):
            fetch_bot_summary(self.user1, "3")

        # Step 2: user2のボットの visibility を partial に変更
        input_data = PartialVisibilityInput(
            target_shared_scope="partial",
            target_allowed_user_ids=["user1"],
            target_allowed_group_ids=[],
        )
        modify_bot_visibility(self.user2, "3", input_data)

        # Step 3: user1が再度fetch_bot_summaryし、成功する
        # このタイミングでAliasが作成される
        summary = fetch_bot_summary(self.user1, "3")
        self.assertEqual(summary.id, "3")

        # Step 4: fetch_all_bots で private ボットを取得
        user1_private_bots = fetch_all_bots(self.user1, kind="private", limit=10)
        self.assertEqual(len(user1_private_bots), 2)

        # Step 5: fetch_all_bots を mixed で取得 (エイリアスが含まれる)
        user1_mixed_bots = fetch_all_bots(self.user1, kind="mixed", limit=10)
        self.assertEqual(len(user1_mixed_bots), 3)  # 自分のボット2つ + user2のエイリアス

        # Step 6: fetch_all_pinned_bots でピン留めボット確認 (0個のはず)
        pinned_bots = fetch_all_pinned_bots(self.user1)
        self.assertEqual(len(pinned_bots), 0)

        # Step 7: user1が自分のボットと user2 のエイリアスにスターをつける
        modify_star_status(self.user1, "1", True)
        modify_star_status(self.user1, "3", True)

        starred_bots = fetch_all_bots(self.user1, starred=True, kind="mixed")
        self.assertEqual(len(starred_bots), 2)

        # Step 8: 管理者が user2 のボットの1つを public にし、ピン留め
        modify_bot_visibility(
            self.admin,
            "3",
            AllVisibilityInput(target_shared_scope="all"),
        )
        modify_pinning_status("3", PushBotInputPinned(to_pinned=True, order=1))

        # Step 9: fetch_all_pinned_bots で確認 (1個増えるはず)
        pinned_bots = fetch_all_pinned_bots(self.user1)
        self.assertEqual(len(pinned_bots), 1)
        self.assertEqual(pinned_bots[0].id, "3")

        # Step 10: fetch_all_bots mixed で取得 (pinnedボットが除外される)
        mixed_bots_after_pin = fetch_all_bots(self.user1, kind="mixed", limit=10)
        self.assertEqual(len(mixed_bots_after_pin), 2)

        # Step 11: user1のボットのパーミッションを変更し、user2がアクセス不可に
        summary = fetch_bot_summary(self.user1, "4")
        self.assertEqual(summary.id, "4")
        bots = fetch_all_bots(self.user1, kind="mixed", limit=10)
        self.assertEqual(len(bots), 3)

        modify_bot_visibility(
            self.user2,
            "4",
            PrivateVisibilityInput(target_shared_scope="private"),
        )

        # Step 12: user1がuser2のボットにアクセスしようとすると失敗
        with self.assertRaises(PermissionError):
            fetch_bot(self.user1, "4")

        # Step 13: fetch_all_bots で mixed 取得し、ボットメタはアクセス不可
        user1_mixed_bots = fetch_all_bots(self.user1, kind="mixed", limit=10)
        for bot_meta in user1_mixed_bots:
            if bot_meta.id == "4":
                self.assertFalse(bot_meta.available)  # アクセス不可を確認


if __name__ == "__main__":
    unittest.main()
