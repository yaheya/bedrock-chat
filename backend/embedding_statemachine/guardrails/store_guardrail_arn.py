import json
import logging
import os
from typing import List, TypedDict

import boto3
from app.repositories.common import decompose_sk
from app.repositories.custom_bot import update_guardrails_params
from app.routes.schemas.bot import type_sync_status

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class StackOutput(TypedDict):
    GuardrailArn: str
    GuardrailVersion: str


def handler(event, context):
    logger.info(f"Event: {event}")
    pk = event["pk"]
    sk = event["sk"]
    stack_output: List[StackOutput] = event["stack_output"]

    # Check if stack_output is valid and has at least one item
    if not stack_output or not isinstance(stack_output, list) or len(stack_output) == 0:
        logger.warning("Empty or invalid stack_output received")
        guardrail_arn = ""
        guardrail_version = ""
    else:
        # Access the first item directly since we know it exists
        first_output = stack_output[0]
        guardrail_arn = first_output.get("GuardrailArn", "")
        guardrail_version = first_output.get("GuardrailVersion", "")

    user_id = pk
    bot_id = decompose_sk(sk)

    update_guardrails_params(user_id, bot_id, guardrail_arn, guardrail_version)
