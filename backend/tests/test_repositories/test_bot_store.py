import sys
import unittest

sys.path.append(".")

from app.repositories.bot_store import find_bots_by_query


class TestBotStore(unittest.TestCase):
    # TODO
    def test_find_bots_by_query(self):
        # Arrange
        query = "query"
        user_id = "user_id"
        limit = 10

        # Act
        result = find_bots_by_query(query, user_id, limit)

        # Assert
        self.assertEqual(result, None)


if __name__ == "__main__":
    unittest.main()
