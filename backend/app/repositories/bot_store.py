import logging

from app.repositories.common import get_opensearch_client
from app.repositories.models.custom_bot import BotMeta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def find_bots_by_query(
    query: str,
    user_id: str,
    limit: int = 20,
) -> list[BotMeta]:
    """Search bots by query string.
    This method is used for bot-store functionality.
    """
    client = get_opensearch_client()
    logger.info(f"Searching bots with query: {query}")

    """
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
                        "should": [
                            {"term": {"SharedScope.keyword": "all"}},
                            {
                                "bool": {
                                    "must": [
                                        {"term": {"SharedScope.keyword": "partial"}},
                                        {
                                            "term": {
                                                "AllowedCognitoUsers.keyword": user_id
                                            }
                                        },
                                    ]
                                }
                            },
                            {
                                "bool": {
                                    "must": [
                                        {
                                            "bool": {
                                                "must_not": {
                                                    "exists": {"field": "SharedScope"}
                                                }
                                            }
                                        },
                                        {"term": {"PK.keyword": user_id}},
                                    ]
                                }
                            },
                        ],
                        "minimum_should_match": 1,
                    }
                },
            }
        },
        "size": limit,
    }

    try:
        response = client.search(index="bot", body=search_body)
        logger.debug(f"Search response: {response}")

        bots = [
            BotMeta.from_opensearch_response(hit, user_id)
            for hit in response["hits"]["hits"]
        ]
        logger.info(f"Found {len(bots)} bots matching query: {query}")
        return bots

    except Exception as e:
        logger.error(f"Error searching bots: {e}")
        raise
