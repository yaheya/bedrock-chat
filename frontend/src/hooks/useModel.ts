import { create } from 'zustand';
import { Model } from '../@types/conversation';
import { useEffect, useMemo, useCallback, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import useLocalStorage from './useLocalStorage';
import { ModelActivate } from '../@types/bot';
import { MODEL_KEYS } from '../constants';
import { 
  toCamelCase
} from '../utils/StringUtils';

const MISTRAL_ENABLED: boolean =
  import.meta.env.VITE_APP_ENABLE_MISTRAL === 'true';

const CLAUDE_SUPPORTED_MEDIA_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

const NOVA_SUPPORTED_MEDIA_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
]

const useModelState = create<{
  modelId: Model;
  setModelId: (m: Model) => void;
}>((set) => ({
  modelId: 'claude-v3-haiku',
  setModelId: (m) => {
    set({
      modelId: m,
    });
  },
}));

const DEFAULT_MODEL: Model = 'claude-v3-haiku';

// Store the Previous BotId
const usePreviousBotId = (botId: string | null | undefined) => {
  const ref = useRef<string | null | undefined>();
  
  useEffect(() => {
    ref.current = botId;
  }, [botId]);
  
  return ref.current;
};

const useModel = (botId?: string | null, modelActivate?: ModelActivate) => {
  const processedModelActivate = useMemo(() => {
    // Early return if modelActivate is provided and not empty
    if (modelActivate && Object.keys(modelActivate).length > 0) {
      return modelActivate;
    }

    // Create a new object with all models set to true
    return MODEL_KEYS.reduce((acc, model) => {
      // Optimize string replacement by doing it in one operation
      acc[toCamelCase(model)] = true;
      return acc;
    }, {} as ModelActivate);
    
  }, [modelActivate]);


  const { t } = useTranslation();
  const previousBotId = usePreviousBotId(botId);

  const availableModels = useMemo<
    {
      modelId: Model;
      label: string;
      supportMediaType: string[];
      description?: string;
    }[]
  >(() => {
    return !MISTRAL_ENABLED
      ? [
          {
            modelId: 'claude-v3-haiku',
            label: t('model.haiku3.label'),
            description: t('model.haiku3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'claude-v3.5-haiku',
            label: t('model.haiku3-5.label'),
            description: t('model.haiku3-5.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'claude-v3-sonnet',
            label: t('model.sonnet3.label'),
            description: t('model.sonnet3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'claude-v3.5-sonnet',
            label: t('model.sonnet3-5.label'),
            description: t('model.sonnet3-5.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'claude-v3.5-sonnet-v2',
            label: t('model.sonnet3-5-v2.label'),
            description: t('model.sonnet3-5-v2.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'claude-v3-opus',
            label: t('model.opus3.label'),
            description: t('model.opus3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
          },
          // New Amazon Nova models
          {
            modelId: 'amazon-nova-pro',
            label: t('model.novaPro.label'),
            description: t('model.novaPro.description'),
            supportMediaType: NOVA_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'amazon-nova-lite',
            label: t('model.novaLite.label'),
            description: t('model.novaLite.description'),
            supportMediaType: NOVA_SUPPORTED_MEDIA_TYPES,
          },
          {
            modelId: 'amazon-nova-micro',
            label: t('model.novaMicro.label'),
            description: t('model.novaMicro.description'),
            supportMediaType: [],
          }
        ]
      : [
          {
            modelId: 'mistral-7b-instruct',
            label: t('model.mistral7b.label'),
            supportMediaType: [],
          },
          {
            modelId: 'mixtral-8x7b-instruct',
            label: t('model.mistral8x7b.label'),
            supportMediaType: [],
          },
          {
            modelId: 'mistral-large',
            label: t('model.mistralLarge.label'),
            supportMediaType: [],
          },
        ];
  }, [t]);

  const [filteredModels, setFilteredModels] = useState(availableModels);
  const { modelId, setModelId } = useModelState();
  const [recentUseModelId, setRecentUseModelId] = useLocalStorage(
    'recentUseModelId',
    DEFAULT_MODEL
  );

  // Save the model id by each bot
  const [botModelId, setBotModelId] = useLocalStorage(
    botId ? `bot_model_${botId}` : 'temp_model',
    ''
  );

  // Update filtered models when modelActivate changes
  useEffect(() => {
    if (MISTRAL_ENABLED) {
      setFilteredModels(availableModels)
    } else if (processedModelActivate) {
      const filtered = availableModels.filter(model => {
        const key = toCamelCase(model.modelId) as keyof ModelActivate;
        return processedModelActivate[key] !== false;
      });
      setFilteredModels(filtered);
    }
  }, [processedModelActivate, availableModels]);

  const getDefaultModel = useCallback(() => {
    // check default model is available
    const defaultModelAvailable = filteredModels.some(m => m.modelId === DEFAULT_MODEL);
    if (defaultModelAvailable) {
      return DEFAULT_MODEL;
    }
    // If the default model is not available, select the first model on the list
    return filteredModels[0]?.modelId ?? DEFAULT_MODEL;
  }, [filteredModels]);

  // select the model via list of modelActivate 
  const selectModel = useCallback((targetModelId: Model) => {
    const modelExists = filteredModels.some(m => toCamelCase(m.modelId) === toCamelCase(targetModelId));
    return modelExists ? targetModelId : getDefaultModel();
  }, [filteredModels, getDefaultModel]);

  useEffect(() => {
    if (processedModelActivate === undefined) {return}

    // botId is changed
    if (previousBotId !== botId) {

      // BotId is undefined, select recent modelId
      if (!botId) {
        setModelId(selectModel(recentUseModelId as Model));
        return;
      }

      // get botModelId from localStorage
      // When acquired from botModelID, settings for previousBotID are acquired, so a key is specified and acquired directly from local storage.
      const botModelId = localStorage.getItem(`bot_model_${botId}`);

      // modelId is in the the LocalStorage. use the saved modelId.
      if (botModelId) {
        setModelId(selectModel(botModelId as Model));
      } else {
        // If there is no bot-specific model ID, check if the last model used can be used
        const lastModelAvailable = filteredModels.some(m => m.modelId === recentUseModelId);

        // If the last model used is available, use it.
        if (lastModelAvailable) {
          setModelId(selectModel(recentUseModelId as Model));
          return;
        }else{
          // Use the default model if not available
          setModelId(selectModel(getDefaultModel()));
        }
      }
    }else{
      // Processing when botId and previousBotID are the same, but there is an update in FilteredModels
      if (botId) {
        const lastModelAvailable = filteredModels.some(m => toCamelCase(m.modelId) === toCamelCase(recentUseModelId) || toCamelCase(m.modelId) === toCamelCase(botModelId) );
        if (!lastModelAvailable) {
          setModelId(selectModel(getDefaultModel()));
        }else{
          setModelId(selectModel(recentUseModelId as Model));
        }
      }
    }
  }, [botId, previousBotId, botModelId, recentUseModelId, modelId, filteredModels, setModelId, selectModel, getDefaultModel, processedModelActivate]);

  const model = useMemo(() => {
    return filteredModels.find((model) => toCamelCase(model.modelId) === toCamelCase(modelId));
  }, [filteredModels, modelId]);

  return {
    modelId,
    setModelId: (model: Model) => {
      setRecentUseModelId(model);
      if (botId) {
        setBotModelId(model);
      }
      setModelId(model);
    },
    model,
    disabledImageUpload: (model?.supportMediaType.length ?? 0) === 0,
    acceptMediaType:
      model?.supportMediaType.flatMap((mediaType) => {
        const ext = mediaType.split('/')[1];
        return ext === 'jpeg' ? ['.jpg', '.jpeg'] : [`.${ext}`];
      }) ?? [],
    availableModels: filteredModels,
  };
};

export default useModel;
