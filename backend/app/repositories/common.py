import json
import os
from typing import Literal

import boto3

DDB_ENDPOINT_URL = os.environ.get("DDB_ENDPOINT_URL")
CONVERSATION_TABLE_NAME = os.environ.get("CONVERSATION_TABLE_NAME", "")
BOT_TABLE_NAME = os.environ.get("BOT_TABLE_NAME", "")
ACCOUNT = os.environ.get("ACCOUNT", "")
REGION = os.environ.get("REGION", "ap-northeast-1")
TABLE_ACCESS_ROLE_ARN = os.environ.get("TABLE_ACCESS_ROLE_ARN", "")
TRANSACTION_BATCH_SIZE = 25

type_table = Literal["conversation", "bot"]
_table_name_map = {"conversation": CONVERSATION_TABLE_NAME, "bot": BOT_TABLE_NAME}


class RecordNotFoundError(Exception):
    pass


class RecordAccessNotAllowedError(Exception):
    pass


class ResourceConflictError(Exception):
    pass


def compose_conv_id(user_id: str, conversation_id: str):
    # Add user_id prefix for row level security to match with `LeadingKeys` condition
    return f"{user_id}#CONV#{conversation_id}"


def decompose_conv_id(conv_id: str):
    return conv_id.split("#")[-1]


def compose_bot_id(user_id: str, bot_id: str):
    # Add user_id prefix for row level security to match with `LeadingKeys` condition
    return f"{user_id}#BOT#{bot_id}"


def decompose_bot_id(composed_bot_id: str):
    return composed_bot_id.split("#")[-1]


def compose_bot_alias_id(user_id: str, alias_id: str):
    # Add user_id prefix for row level security to match with `LeadingKeys` condition
    return f"{user_id}#BOT_ALIAS#{alias_id}"


def decompose_bot_alias_id(composed_alias_id: str):
    return composed_alias_id.split("#")[-1]


def compose_related_document_source_id(
    user_id: str,
    conversation_id: str,
    source_id: str,
):
    # Add user_id prefix for row level security to match with `LeadingKeys` condition
    return f"{user_id}#RELATED_DOCUMENT#{conversation_id}#{source_id}"


def decompose_related_document_source_id(composed_id: str):
    return composed_id.split("#")[-1]


def _get_aws_resource(service_name, table_name: str, user_id=None):
    """Get AWS resource with optional row-level access control for DynamoDB.
    Ref: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_dynamodb_items.html
    """
    if "AWS_EXECUTION_ENV" not in os.environ:
        if DDB_ENDPOINT_URL:
            return boto3.resource(
                service_name,
                endpoint_url=DDB_ENDPOINT_URL,
                aws_access_key_id="key",
                aws_secret_access_key="key",
                region_name=REGION,
            )
        else:
            return boto3.resource(service_name, region_name=REGION)

    policy_document = {
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:BatchGetItem",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:ConditionCheckItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:DescribeTable",
                    "dynamodb:GetItem",
                    "dynamodb:GetRecords",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:UpdateItem",
                ],
                "Resource": [
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/{table_name}",
                    f"arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/{table_name}/index/*",
                ],
            }
        ]
    }
    if user_id:
        policy_document["Statement"][0]["Condition"] = {
            # Allow access to items with the same partition key as the user id
            "ForAllValues:StringLike": {"dynamodb:LeadingKeys": [f"{user_id}*"]}
        }

    sts_client = boto3.client("sts")
    assumed_role_object = sts_client.assume_role(
        RoleArn=TABLE_ACCESS_ROLE_ARN,
        RoleSessionName="DynamoDBSession",
        Policy=json.dumps(policy_document),
    )
    credentials = assumed_role_object["Credentials"]
    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
    return session.resource(service_name, region_name=REGION)


def _get_dynamodb_client(user_id=None, table_type: type_table = "conversation"):
    """Get a DynamoDB client, optionally with row-level access control."""
    if table_type == "bot":
        # Bot table does not have row-level access control
        user_id = None
    return _get_aws_resource(
        "dynamodb", user_id=user_id, table_name=_table_name_map[table_type]
    ).meta.client


def _get_table_client(user_id, table_type: type_table = "conversation"):
    """Get a DynamoDB table client with row-level access."""
    if table_type == "bot":
        # Bot table does not have row-level access control
        user_id = None
    return _get_aws_resource(
        "dynamodb", user_id=user_id, table_name=_table_name_map[table_type]
    ).Table(_table_name_map[table_type])


def _get_table_public_client(table_type: type_table = "conversation"):
    """Get a DynamoDB table client.
    Warning: No row-level access. Use for only limited use case.
    """
    return _get_aws_resource("dynamodb", table_name=_table_name_map[table_type]).Table(
        _table_name_map[table_type]
    )
