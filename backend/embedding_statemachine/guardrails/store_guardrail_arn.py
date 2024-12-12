import json
import logging
import os
from typing import TypedDict

from app.repositories.common import decompose_sk
from app.repositories.custom_bot import update_guardrails_params
from retry import retry

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class StackOutput(TypedDict):
    KnowledgeBaseId: str
    DataSourceId: str
    GuardrailArn: str
    GuardrailVersion: str


def handler(event, context):
    logger.info(f"Event: {event}")
    pk = event["pk"]
    sk = event["sk"]
    stack_output: list[StackOutput] = event["stack_output"]

    guardrail_arn = stack_output[0]["GuardrailArn"]
    guardrail_version = stack_output[0]["GuardrailVersion"]

    user_id = pk
    bot_id = decompose_sk(sk)

    update_guardrails_params(user_id, bot_id, guardrail_arn, guardrail_version)
