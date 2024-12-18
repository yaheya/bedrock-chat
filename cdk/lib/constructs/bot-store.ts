import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { generatePhysicalName } from "../utils/generate-physical-name";
import * as logs from "aws-cdk-lib/aws-logs";
import * as oss from "aws-cdk-lib/aws-opensearchserverless";
import * as osis from "aws-cdk-lib/aws-osis";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
  HttpMethods,
  ObjectOwnership,
} from "aws-cdk-lib/aws-s3";
import { RemovalPolicy, Stack } from "aws-cdk-lib";
import { Effect, Policy, PolicyStatement, Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";

export type Language = 
  | "en"
  | "de"
  | "fr"
  | "es"
  | "ja"
  | "ko"
  | "zhhans"
  | "zhhant"
  | "it"
  | "nb"
  | "th"
  | "id"
  | "ms";

export interface BotStoreProps {
  readonly botTable: dynamodb.ITable;
  readonly useStandbyReplicas: boolean;
  readonly language: Language;
}

export class BotStore extends Construct {
  constructor(scope: Construct, id: string, props: BotStoreProps) {
    super(scope, id);

    const collectionName = generatePhysicalName(this, "Collection", {
      maxLength: 32,
      lower: true,
    });

    const standbyReplicas: props.useStandbyReplicas === true ? "ENABLED" : "DISABLED";

    const networkPolicy = new oss.CfnSecurityPolicy(this, "NetworkPolicy", {
      name: generatePhysicalName(this, "NetworkPolicy", {
        maxLength: 32,
        lower: true,
      }),
      type: "network",
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: "collection",
              Resource: [`collection/${collectionName}`],
            },
            {
              ResourceType: "dashboard",
              Resource: [`collection/${collectionName}`],
            },
          ],
          AllowFromPublic: true,
        },
      ]),
    });

    const encryptionPolicy = new oss.CfnSecurityPolicy(
      this,
      "EncryptionPolicy",
      {
        name: generatePhysicalName(this, "EncryptionPolicy", {
          maxLength: 32,
          lower: true,
        }),
        type: "encryption",
        policy: JSON.stringify({
          Rules: [
            {
              ResourceType: "collection",
              Resource: [`collection/${collectionName}`],
            },
          ],
          AWSOwnedKey: true,
        }),
      }
    );

    const collection = new oss.CfnCollection(this, "Collection", {
      name: collectionName,
      // type: 'VECTORSEARCH',
      type: "SEARCH",
      standbyReplicas
    });

    const endpoint = collection.getAtt("CollectionEndpoint").toString();

    const bucket = new Bucket(this, "Bucket", {
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      objectOwnership: ObjectOwnership.OBJECT_WRITER,
      autoDeleteObjects: true,
    });

    const ingestionLogGroup = new logs.LogGroup(this, "IngensionLogGroup", {
      logGroupName: `/aws/vendedlogs/OpenSearchIngestion/bot-table-osis-pipeline/${id}`.toLowerCase(),
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.ONE_WEEK,
    });

    const osisRole = new Role(this, "OsisRole", {
      assumedBy: new ServicePrincipal("osis-pipelines.amazonaws.com"),
    });
    const osisPolicy = new Policy(this, "OsisPolicy", {
      statements: [
        new PolicyStatement({
          sid: "allowRunExportJob",
          effect: Effect.ALLOW,
          actions: [
            "dynamodb:DescribeTable",
            "dynamodb:DescribeContinuousBackups",
            "dynamodb:ExportTableToPointInTime",
          ],
          resources: [props.botTable.tableArn],
        }),
        new PolicyStatement({
          sid: "allowCheckExportjob",
          effect: Effect.ALLOW,
          actions: ["dynamodb:DescribeExport"],
          resources: [`${props.botTable.tableArn}/export/*`],
        }),
        new PolicyStatement({
          sid: "allowReadFromStream",
          effect: Effect.ALLOW,
          actions: [
            "dynamodb:DescribeStream",
            "dynamodb:GetRecords",
            "dynamodb:GetShardIterator",
          ],
          resources: [`${props.botTable.tableArn}/stream/*`],
        }),
        new PolicyStatement({
          sid: "allowReadAndWriteToS3ForExport",
          effect: Effect.ALLOW,
          actions: [
            "s3:GetObject",
            "s3:AbortMultipartUpload",
            "s3:PutObject",
            "s3:PutObjectAcl",
          ],
          resources: [`${bucket.bucketArn}/*`],
        }),
        new PolicyStatement({
          effect: Effect.ALLOW,
          actions: [
            "aoss:APIAccessAll",
            "aoss:BatchGetCollection",
            "aoss:CreateSecurityPolicy",
            "aoss:GetSecurityPolicy",
            "aoss:UpdateSecurityPolicy",
            "es:DescribeDomain",
            "es:ESHttp*",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
          ],
          resources: ["*"],
        }),
        new PolicyStatement({
          effect: Effect.ALLOW,
          actions: [
            "logs:CreateLogDelivery",
            "logs:PutResourcePolicy",
            "logs:UpdateLogDelivery",
            "logs:DeleteLogDelivery",
            "logs:DescribeResourcePolicies",
            "logs:GetLogDelivery",
            "logs:ListLogDeliveries",
          ],
          resources: ["*"],
        }),
      ],
    });
    osisPolicy.attachToRole(osisRole);

    const dataAccessPolicy = new oss.CfnAccessPolicy(this, "DataAccessPolicy", {
      name: generatePhysicalName(this, "DataAccessPolicy", {
        maxLength: 32,
        lower: true,
      }),
      type: "data",
      description: `Data access policy for ${collectionName} collection.`,
      policy: `
        [
          {
            "Rules": [
              {
                "ResourceType": "collection",
                "Resource": ["collection/${collectionName}"],
                "Permission": [
                  "aoss:CreateCollectionItems",
                  "aoss:DescribeCollectionItems",
                  "aoss:DeleteCollectionItems",
                  "aoss:UpdateCollectionItems"
                ]
              },
              {
                "ResourceType": "index",
                "Resource": ["index/${collectionName}/*"],
                "Permission": [
                  "aoss:CreateIndex",
                  "aoss:DeleteIndex",
                  "aoss:UpdateIndex",
                  "aoss:DescribeIndex",
                  "aoss:ReadDocument",
                  "aoss:WriteDocument"
                ]
              }
            ],
            "Principal": [
              "${osisRole.roleArn}"
            ]
          }
        ]
      `,
    });

    collection.addDependency(encryptionPolicy);
    collection.addDependency(networkPolicy);
    collection.addDependency(dataAccessPolicy);

    const osisPipelineConfig = {
      version: "2",
      "dynamodb-pipeline": {
        source: {
          dynamodb: {
            acknowledgments: true,
            tables: [
              {
                table_arn: props.botTable.tableArn,
                stream: {
                  start_position: "LATEST",
                },
                export: {
                  s3_bucket: bucket.bucketName,
                  s3_region: Stack.of(this).region,
                },
              },
            ],
            aws: {
              sts_role_arn: osisRole.roleArn,
              region: Stack.of(this).region,
            },
          },
        },
        sink: [
          {
            opensearch: {
              hosts: [endpoint],
              index: "bot",
              ...(props.language === "en"
                ? {} // For en, index_type, template_type, template_content are not required
                : {
                    index_type: "custom",
                    template_type: "index-template",
                    template_content: this.genTemplateContent(props.language),
                  }),
              document_id: "${getMetadata(\"primary_key\")}",
              action: "${getMetadata(\"opensearch_action\")}",
              document_version: "${getMetadata(\"document_version\")}",
              document_version_type: "external",
              aws: {
                sts_role_arn: osisRole.roleArn,
                region: Stack.of(this).region,
                serverless: true,
              },
            },
          },
        ],
      },
    };

    new osis.CfnPipeline(this, "OsisPipeline", {
      pipelineName: generatePhysicalName(this, "OsisPipeline", {
        maxLength: 32,
        lower: true,
      }),
      minUnits: 1,
      maxUnits: 4,
      logPublishingOptions: {
        isLoggingEnabled: true,
        cloudWatchLogDestination: {
          logGroup: ingestionLogGroup.logGroupName,
        },
      },
      // Ref: https://opensearch.org/docs/latest/data-prepper/pipelines/configuration/sinks/opensearch/
      pipelineConfigurationBody: JSON.stringify(osisPipelineConfig),
    });
  }

  private genTemplateContent(language: Language): string {
    switch (language) {
      case "ja":
        return JSON.stringify({
          template: {
            settings: {
              analysis: {
                analyzer: {
                  ja_analyzer: {
                    type: "custom",
                    char_filter: ["icu_normalizer"],
                    tokenizer: "kuromoji_tokenizer",
                    filter: [
                      "kuromoji_baseform",
                      "kuromoji_part_of_speech",
                      "ja_stop",
                      "kuromoji_number",
                      "kuromoji_stemmer",
                    ],
                  },
                },
              },
            },
          },
        });
  
      default:
        throw new Error(`Unsupported language: ${language}`);
    }
  }
}
