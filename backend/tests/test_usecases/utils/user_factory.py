import os
import sys
import time
import uuid

import boto3
from botocore.exceptions import ClientError

USER_POOL_ID = os.environ.get("USER_POOL_ID")
REGION = os.environ.get("REGION")
cognito_client = boto3.client("cognito-idp", region_name=REGION)

sys.path.append(".")

from app.user import User


def _create_email_from_id(user_id: str) -> str:
    return f"{user_id}@example.com"


def store_user_in_cognito(user: User) -> None:
    """
    Cognitoにユーザーを保存する関数。

    Args:
        user (User): 作成するUserオブジェクト
    """
    try:
        cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user.email,
            UserAttributes=[
                {"Name": "name", "Value": user.email},
                # {
                #     "Name": "cognito:groups",
                #     "Value": ",".join(user.groups) if user.groups else "",
                # },
                # {"Name": "email_verified", "Value": "true"},
            ],
            DesiredDeliveryMediums=["EMAIL"],
            ForceAliasCreation=False,
            MessageAction="SUPPRESS",  # 通知メールを送らない
        )
        print(f"ユーザー '{user.name}' がCognitoに保存されました。")
    except cognito_client.exceptions.UsernameExistsException:
        # 既に存在する場合はスキップ
        print(f"ユーザー '{user.name}' は既にCognitoに存在しています。")

    # # ユーザーの存在確認とリトライ処理
    # for _ in range(5):  # 最大5回リトライ
    #     try:
    #         cognito_client.admin_get_user(UserPoolId=USER_POOL_ID, Username=email)
    #         print(f"ユーザー '{user.id}' が存在します。グループ追加を実行します。")
    #         break
    #     except cognito_client.exceptions.UserNotFoundException:
    #         print(f"ユーザー '{user.id}' が見つかりません。再試行します...")
    #         time.sleep(2)  # 2秒待機
    # else:
    #     raise Exception(
    #         f"ユーザー '{user.id}' が作成後に見つかりません。処理を中断します。"
    #     )

    try:
        for group in user.groups:
            cognito_client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID, Username=user.email, GroupName=group
            )
            print(f"ユーザー '{user.name}' がグループ '{group}' に追加されました。")
    except ClientError as e:
        print(f"グループ追加中にエラー: {e}")
        raise e


def delete_cognito_user(user: User):
    """
    Cognitoのユーザーを削除する関数。

    Args:
        user_name (str): 削除するユーザー名
    """
    try:
        cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=user.email)
        print(f"ユーザー '{user.name}' がCognitoから削除されました。")
    except ClientError as e:
        print(f"ユーザー削除中にエラーが発生しました: {e}")
        raise e


def create_test_user(user_name: str) -> User:
    return User(
        id=user_name,
        name=user_name,
        email=_create_email_from_id(user_name),
        groups=[],
    )


def create_test_admin_user(user_name: str) -> User:
    return User(
        id=user_name,
        name=user_name,
        email=_create_email_from_id(user_name),
        groups=["Admin"],
    )
