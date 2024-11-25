import { BedrockKnowledgeBase } from '../features/knowledgeBase/types';

export type BotKind = 'private' | 'mixed';

export type ModelActivate = {
  // # Claude models
  claude3SonnetV1?: boolean;
  claude3HaikuV1?: boolean;
  claude3OpusV1?: boolean;
  claude35SonnetV1?: boolean;
  claude35SonnetV2?: boolean;
  claude35HaikuV1?: boolean;

  // Mistral models
  mistral7b?: boolean
  mistral8x7b?: boolean
  mistralLarge?: boolean
};

export type BotMeta = {
  id: string;
  title: string;
  description: string;
  createTime: Date;
  lastUsedTime: Date;
  isPublic: boolean;
  isPinned: boolean;
  owned: boolean;
  syncStatus: BotSyncStatus;
};

export type BotKnowledge = {
  sourceUrls: string[];
  // Sitemap cannot be used yet.
  sitemapUrls: string[];
  filenames: string[];
  s3Urls: string[];
};

export type ConversationQuickStarter = {
  title: string;
  example: string;
};

export type BotKnowledgeDiff = {
  sourceUrls: string[];
  // Sitemap cannot be used yet.
  sitemapUrls: string[];
  addedFilenames: string[];
  deletedFilenames: string[];
  unchangedFilenames: string[];
  s3Urls: string[];
};

export type BotSyncStatus = 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';

export type BotListItem = BotMeta & {
  available: boolean;
};

export type GenerationParams = {
  maxTokens: number;
  topK: number;
  topP: number;
  temperature: number;
  stopSequences: string[];
};

export type GuardrailsParams = {
  isGuardrailEnabled: boolean;
  hateThreshold: number;
  insultsThreshold: number;
  sexualThreshold: number;
  violenceThreshold: number;
  misconductThreshold: number;
  groundingThreshold: number;
  relevanceThreshold: number;
  guardrailArn: string;
  guardrailVersion: string;
};

export type BotDetails = BotMeta & {
  instruction: string;
  generationParams: GenerationParams;
  agent: Agent;
  knowledge: BotKnowledge;
  syncStatusReason: string;
  displayRetrievedChunks: boolean;
  conversationQuickStarters: ConversationQuickStarter[];
  bedrockGuardrails: GuardrailsParams;
  bedrockKnowledgeBase: BedrockKnowledgeBase;
  modelActivate: ModelActivate;
};

export type BotSummary = BotMeta & {
  hasKnowledge: boolean;
  hasAgent: boolean;
  conversationQuickStarters: ConversationQuickStarter[];
  modelActivate: ModelActivate;
};

export type BotFile = {
  filename: string;
  status: 'UPLOADING' | 'UPLOADED' | 'ERROR';
  errorMessage?: string;
  progress?: number;
};

export type RegisterBotRequest = {
  id: string;
  title: string;
  instruction: string;
  agent: AgentInput;
  description?: string;
  generationParams?: GenerationParams;
  knowledge?: BotKnowledge;
  displayRetrievedChunks: boolean;
  conversationQuickStarters: ConversationQuickStarter[];
  bedrockGuardrails?: GuardrailsParams;
  bedrockKnowledgeBase?: BedrockKnowledgeBase;
  modelActivate?: ModelActivate;
};

export type RegisterBotResponse = BotDetails;

export type UpdateBotRequest = {
  title: string;
  instruction: string;
  description?: string;
  agent: AgentInput;
  generationParams?: BotGenerationConfig;
  knowledge?: BotKnowledgeDiff;
  displayRetrievedChunks: boolean;
  conversationQuickStarters: ConversationQuickStarter[];
  bedrockGuardrails?: GuardrailsParams;
  bedrockKnowledgeBase?: BedrockKnowledgeBase;
  modelActivate?: ModelActivate;
};

export type UpdateBotResponse = {
  id: string;
  title: string;
  instruction: string;
  description: string;
  generationParams: GenerationParams;
  knowledge?: BotKnowledge;
  displayRetrievedChunks: boolean;
  conversationQuickStarters: ConversationQuickStarter[];
  bedrockKnowledgeBase: BedrockKnowledgeBase;
  modelActivate: ModelActivate;
};

export type UpdateBotPinnedRequest = {
  pinned: boolean;
};

export type UpdateBotPinnedResponse = null;

export type UpdateBotVisibilityRequest = {
  toPublic: boolean;
};

export type UpdateBotVisibilityResponse = null;

export type GetBotsRequest =
  | {
      kind: 'private';
      limit?: number;
    }
  | {
      kind: 'mixed';
      limit: number;
    }
  | {
      kind: 'mixed';
      pinned: boolean;
    };

export type GetBotsResponse = BotListItem[];

export type GetMyBotResponse = BotDetails;

export type GetBotSummaryResponse = BotSummary;

export type GetPublicBotResponse = BotDetails;

export type GetPresignedUrlResponse = {
  url: string;
};
