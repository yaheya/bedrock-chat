import logging

from app.repositories.common import get_opensearch_client
from app.repositories.models.custom_bot import BotMeta
from app.user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def find_bots_by_query(
    query: str,
    user: User,
    limit: int = 20,
) -> list[BotMeta]:
    """Search bots by query string.
    This method is used for bot-store functionality.


    Query Structure Explanation:

    1. Main Search (must clause):
    - Uses multi_match for flexible text searching
    - Searches across multiple fields (Description, Title, Instruction)
    - Implements fuzzy matching for typo tolerance
    - Requires 50% of search terms to match

    2. Access Control (filter clause):
    The filter implements three access levels:
    a) Public Access:
        - Matches documents with SharedScope = "all"
        - Available to all users

    b) Partial Access:
        - Matches documents with SharedScope = "partial"
        - User must be in AllowedCognitoUsers list

    c) Private Access:
        - Matches documents with no SharedScope field
        - Only accessible to the owner (PK matches user_id)
    """
    client = get_opensearch_client()
    logger.info(f"Searching bots with query: {query}")

    # Create the base filter clause
    filter_must = [{"prefix": {"SK.keyword": "BOT"}}]  # Include only BOT items
    filter_should = [
        {"term": {"SharedScope.keyword": "all"}},
        {
            "bool": {
                "must": [
                    {"bool": {"must_not": {"exists": {"field": "SharedScope"}}}},
                    {"term": {"PK.keyword": user.id}},
                ]
            }
        },
    ]

    # Add partial access filter if not admin
    if not user.is_admin():
        filter_should.insert(
            1,  # Insert the partial access clause after the public access clause
            {
                "bool": {
                    "must": [
                        {"term": {"SharedScope.keyword": "partial"}},
                        {
                            "bool": {
                                "should": [
                                    # If user is in AllowedCognitoUsers
                                    {"term": {"AllowedCognitoUsers.keyword": user.id}},
                                    # If user is in AllowedCognitoGroups
                                    {
                                        "script": {
                                            "script": {
                                                "source": (
                                                    "if (doc['AllowedCognitoGroups.keyword'].size() == 0 || params.user_groups.size() == 0) { "
                                                    "return false; } "
                                                    "for (group in doc['AllowedCognitoGroups.keyword']) { "
                                                    "if (params.user_groups.contains(group)) { return true; } } "
                                                    "return false;"
                                                ),
                                                "params": {"user_groups": user.groups},
                                                "lang": "painless",
                                            }
                                        }
                                    },
                                ],
                                "minimum_should_match": 1,
                            }
                        },
                        # TODO: remove
                        # {"term": {"AllowedCognitoUsers.keyword": user.id}},
                    ]
                }
            },
        )

    search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["Description", "Title", "Instruction"],
                            "type": "best_fields",
                            "operator": "or",
                            "minimum_should_match": "50%",
                            "fuzziness": "AUTO",
                        }
                    }
                ],
                "filter": {
                    "bool": {
                        "must": filter_must,
                        "should": filter_should,
                        "minimum_should_match": 1,
                    }
                },
                "must_not": [
                    {"term": {"ItemType.keyword": "ALIAS"}}  # Exclude ALIAS items
                ],
            }
        },
        "size": limit,
    }
    logger.debug(f"Entire search body: {search_body}")

    try:
        response = client.search(index="bot", body=search_body)
        logger.debug(f"Search response: {response}")

        bots = [
            BotMeta.from_opensearch_response(hit, user.id)
            for hit in response["hits"]["hits"]
        ]
        logger.info(f"Found {len(bots)} bots matching query: {query}")
        return bots

    except Exception as e:
        logger.error(f"Error searching bots: {e}")
        raise


# TODO: remove
# def find_bots_by_query(
#     query: str,
#     user_id: str,
#     limit: int = 20,
#     is_admin = False,
# ) -> list[BotMeta]:
#     """Search bots by query string.
#     This method is used for bot-store functionality.
#     """
#     client = get_opensearch_client()
#     logger.info(f"Searching bots with query: {query}")

#     """
#     Query Structure Explanation:

#     1. Main Search (must clause):
#     - Uses multi_match for flexible text searching
#     - Searches across multiple fields (Description, Title, Instruction)
#     - Implements fuzzy matching for typo tolerance
#     - Requires 50% of search terms to match

#     2. Access Control (filter clause):
#     The filter implements three access levels:
#     a) Public Access:
#         - Matches documents with SharedScope = "all"
#         - Available to all users

#     b) Partial Access:
#         - Matches documents with SharedScope = "partial"
#         - User must be in AllowedCognitoUsers list

#     c) Private Access:
#         - Matches documents with no SharedScope field
#         - Only accessible to the owner (PK matches user_id)
#     """
#     search_body = {
#         "query": {
#             "bool": {
#                 "must": [
#                     {
#                         "multi_match": {
#                             "query": query,
#                             "fields": ["Description", "Title", "Instruction"],
#                             "type": "best_fields",
#                             "operator": "or",
#                             "minimum_should_match": "50%",
#                             "fuzziness": "AUTO",
#                         }
#                     }
#                 ],
#                 "filter": {
#                     "bool": {
#                         "must": [
#                             {"prefix": {"SK.keyword": "BOT"}}
#                         ],  # Note: omit ALIAS items
#                         "should": [
#                             {"term": {"SharedScope.keyword": "all"}},
#                             # {
#                             #     "bool": {
#                             #         "must": [
#                             #             {"term": {"SharedScope.keyword": "partial"}},
#                             #             {
#                             #                 "term": {
#                             #                     "AllowedCognitoUsers.keyword": user_id
#                             #                 }
#                             #             },
#                             #         ]
#                             #     }
#                             # },
#                             {
#                                 "bool": {
#                                     "must": [
#                                         {
#                                             "bool": {
#                                                 "must_not": {
#                                                     "exists": {"field": "SharedScope"}
#                                                 }
#                                             }
#                                         },
#                                         {"term": {"PK.keyword": user_id}},
#                                     ]
#                                 }
#                             },
#                         ],
#                         "minimum_should_match": 1,
#                     }
#                 },
#                 "must_not": [
#                     {"term": {"ItemType.keyword": "ALIAS"}}  # Exclude ALIAS items
#                 ],
#             }
#         },
#         "size": limit,
#     }

#     try:
#         response = client.search(index="bot", body=search_body)
#         logger.debug(f"Search response: {response}")

#         bots = [
#             BotMeta.from_opensearch_response(hit, user_id)
#             for hit in response["hits"]["hits"]
#         ]
#         logger.info(f"Found {len(bots)} bots matching query: {query}")
#         return bots

#     except Exception as e:
#         logger.error(f"Error searching bots: {e}")
#         raise
