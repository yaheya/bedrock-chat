# Migration Guide (v2 to v3)

## TL;DR

- V3 introduces fine-grained permission control and Bot Store functionality, requiring DynamoDB schema changes
- **Backup your DynamoDB ConversationTable before migration**
- Update your repository URL from `bedrock-claude-chat` to `bedrock-chat`
- Run the migration script to convert your data to the new schema
- All your bots and conversations will be preserved with the new permission model

## Introduction

### What's New in V3

V3 introduces significant enhancements to Bedrock Chat:

1. **Fine-grained permission control**: Control access to your bots with user group-based permissions
2. **Bot Store**: Share and discover bots through a centralized marketplace
3. **Administrative features**: Manage APIs, mark bots as essential, and analyze bot usage

These new features required changes to the DynamoDB schema, necessitating a migration process for existing users.

### Why This Migration Is Necessary

The new permission model and Bot Store functionality required restructuring how bot data is stored and accessed. The migration process converts your existing bots and conversations to the new schema while preserving all your data.

## Migration Process

### Step 0: Ensure You're on the Latest V2 Version

Before starting the migration, make sure you're running the latest version of V2. This ensures you have all the necessary bug fixes and improvements before upgrading to V3:

```bash
# Fetch the latest tags
git fetch --tags

# Checkout the latest V2 version
git checkout v2.9.0

# Deploy the latest V2 version
cd cdk
npm ci
npx cdk deploy
```

Running the latest V2 version before migrating to V3 provides a more stable starting point for the migration process.

### Step 1: Backup Your DynamoDB Table

Before proceeding, create a backup of your DynamoDB ConversationTable:

```bash
# Get your table name from CloudFormation outputs
aws dynamodb create-backup \
  --table-name BedrockChatStack-DatabaseConversationTableXXXXXX \
  --backup-name "BedrockChatV2Backup-$(date +%Y%m%d)"
```

### Step 2: Update Repository URL (Recommended)

The repository has been renamed from `bedrock-claude-chat` to `bedrock-chat`. Update your local repository:

```bash
# Check your current remote URL
git remote -v

# Update the remote URL
git remote set-url origin https://github.com/aws-samples/bedrock-chat.git

# Verify the change
git remote -v
```

### Step 3: Pull V3 and Deploy

Pull the latest V3 code and deploy:

```bash
git fetch
git checkout v3
cd cdk
npm ci
npx cdk deploy
```

### Step 4: Run the Migration Script

The migration script will convert your V2 data to the V3 schema. First, edit the script to set your table names:

```bash
# Navigate to the migration directory
cd docs/migration

# Edit migrate_v2_v3.py to update:
# - V2_CONVERSATION_TABLE
# - V3_CONVERSATION_TABLE
# - V3_BOT_TABLE
```

Then run the script using Poetry from the backend directory:

```bash
# Navigate to the backend directory
cd ../../backend

# Install dependencies if you haven't already
poetry install

# Run a dry run first to see what would be migrated
poetry run python ../docs/migration/migrate_v2_v3.py --dry-run

# If everything looks good, run the actual migration
poetry run python ../docs/migration/migrate_v2_v3.py

# Verify the migration was successful
poetry run python ../docs/migration/migrate_v2_v3.py --verify-only
```

The migration script will generate a report file with details about the migration process. Check this file to ensure all your data was migrated correctly.

#### Handling Large Data Volumes

For environments with heavy users or large amounts of data, consider these approaches:

1. **Migrate users individually**: For users with large data volumes, migrate them one at a time:

   ```bash
   poetry run python ../docs/migration/migrate_v2_v3.py --users user-id-1 user-id-2
   ```

2. **Memory considerations**: The migration process loads data into memory. If you encounter Out-Of-Memory (OOM) errors, try:

   - Migrating one user at a time
   - Running the migration on a machine with more memory
   - Breaking up the migration into smaller batches of users

3. **Monitor the migration**: Check the generated report files to ensure all data is migrated correctly, especially for large datasets.

### Step 5: Verify the Application

After migration, open your application and verify:

- All your bots are available
- Conversations are preserved
- New permission controls are working

## V3 FAQ

### Bot Access and Permissions

**Q: What happens if a bot I'm using is deleted or my access permission is removed?**  
A: Authorization is checked at chat time, so you'll lose access immediately. The ALIAS will be updated with `IsOriginAccessible` set to False.

**Q: What happens if a user is deleted (e.g., employee leaves)?**  
A: Their data can be completely removed by deleting all items with their user ID as the partition key (PK).

**Q: What happens if a pinned public bot is unpinned?**  
A: It will be excluded from the Push-type retrieval API (using GSI-2).

**Q: Can I turn off sharing for a pinned public bot?**  
A: No, you must unpin the bot first before turning off sharing.

**Q: Can I delete a pinned public bot?**  
A: No, you must unpin the bot first before deleting it.

### Security and Implementation

**Q: Is row-level security (RLS) implemented?**  
A: No, considering the diversity of access patterns. Authorization is performed when accessing bots, and the risk of metadata leakage is considered minimal compared to conversation history.

**Q: Is the Bot Store available by default?**  
A: Yes, it's enabled by default in V3.

**Q: What are the requirements for publishing an API?**  
A: The bot must have `SharedScope` set to "PUBLIC".

**Q: Will there be a management screen for all private bots?**  
A: Not in the initial V3 release. However, items can still be deleted by querying with the user ID as needed.

**Q: Will there be tagging functionality?**  
A: Not in the initial V3 release, but LLM-based automatic tagging may be added in future updates.

### Administration

**Q: What can administrators do?**  
A: Administrators can:

- Manage public bots (including checking high-cost bots)
- Manage APIs
- Pin public bots (both fully public and partially public)
- Access all public bots regardless of authorization settings

**Q: Can I pin partially public bots?**  
A: Yes, though the initial version only supports pinning fully public bots.

**Q: Can I set priority for pinned bots?**  
A: Yes, you can set the display order of pinned bots.

### Authorization Configuration

**Q: How do I set up authorization?**  
A:

1. Open the Amazon Cognito console and create user groups in the BrChat user pool
2. Add users to these groups as needed
3. In BrChat, select the user groups you want to allow access to when configuring bot sharing settings

Note: Group membership changes require re-login to take effect. Changes are reflected at token refresh, but not during the ID token validity period (default 30 minutes in V3, configurable in cdk.json).

**Q: Does the system check with Cognito every time a bot is accessed?**  
A: No, authorization is checked using the JWT token to avoid unnecessary I/O operations.

**Q: Can I set permissions for individual users?**  
A: Not in the initial V3 release, though the design allows for this to be added in the future.

### Search Functionality

**Q: Does bot search support semantic search?**  
A: No, only partial text matching is supported. Semantic search (e.g., "automobile" → "car", "EV", "vehicle") is not available due to OpenSearch Serverless constraints.
