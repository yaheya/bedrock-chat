import logging
import os

import boto3
from app.user import User, UserGroup
from botocore.exceptions import ClientError
from retry import retry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

USER_POOL_ID = os.environ.get("USER_POOL_ID")

client = boto3.client("cognito-idp")


@retry(ClientError, tries=3, delay=1)
def find_users_by_email_prefix(prefix: str, limit: int = 10) -> list[User]:
    try:
        response = client.list_users(
            UserPoolId=USER_POOL_ID, Filter=f'email ^= "{prefix}"', Limit=limit
        )
        users = response.get("Users", [])
        return [User.from_cognito_idp_response(user) for user in users]
    except ClientError as e:
        # Retry if rate limit.
        # The quota is 30 RPS for ListUsers.
        # See: https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html
        if e.response["Error"]["Code"] == "TooManyRequestsException":
            logger.warning(f"Rate limit exceeded. Retrying... Error: {e}")
            raise
        else:
            raise


@retry(ClientError, tries=3, delay=1)
def find_group_by_name_prefix(prefix: str) -> list[UserGroup]:
    groups = []
    next_token = None
    MAX_ATTEMPTS = 5

    try:
        for _ in range(MAX_ATTEMPTS):
            params = {"UserPoolId": USER_POOL_ID}
            if next_token:
                params["NextToken"] = next_token

            response = client.list_groups(**params)
            groups.extend(response.get("Groups", []))

            next_token = response.get("NextToken")
            if not next_token:
                break

        if next_token:
            logger.warning(
                f"Reached the maximum retrieval attempts ({MAX_ATTEMPTS}). "
                "Some groups might not have been retrieved."
            )

        # Cognito client does not support prefix filtering.
        # So we need to filter the groups on client side.
        filtered_groups = [
            UserGroup.from_cognito_idp_response(group)
            for group in groups
            if group["GroupName"].startswith(prefix)
        ]
        return filtered_groups

    except ClientError as e:
        # Retry if rate limit.
        # The quota is 20 RPS for ListUsers.
        # See: https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html
        if e.response["Error"]["Code"] == "TooManyRequestsException":
            logger.warning(f"Rate limit exceeded. Retrying... Error: {e}")
            raise
        else:
            raise
