import { create } from 'zustand';
import { Model } from '../@types/conversation';
import { useEffect, useMemo, useCallback, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import useLocalStorage from './useLocalStorage';
import { ModelActivate } from '../@types/bot';

const MISTRAL_ENABLED: boolean =
  import.meta.env.VITE_APP_ENABLE_MISTRAL === 'true';

const CLAUDE_SUPPORTED_MEDIA_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

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
  const { t } = useTranslation();
  const previousBotId = usePreviousBotId(botId);

  const availableModels = useMemo<
    {
      modelId: Model;
      label: string;
      supportMediaType: string[];
      description?: string;
      modelActivateKey: string;
    }[]
  >(() => {
    return !MISTRAL_ENABLED
      ? [
          {
            modelId: 'claude-v3-haiku',
            label: t('model.haiku3.label'),
            description: t('model.haiku3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude3HaikuV1',
          },
          {
            modelId: 'claude-v3.5-haiku',
            label: t('model.haiku3-5.label'),
            description: t('model.haiku3-5.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude35HaikuV1'
          },
          {
            modelId: 'claude-v3-sonnet',
            label: t('model.sonnet3.label'),
            description: t('model.sonnet3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude3SonnetV1'
          },
          {
            modelId: 'claude-v3.5-sonnet',
            label: t('model.sonnet3-5.label'),
            description: t('model.sonnet3-5.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude35SonnetV1'
          },
          {
            modelId: 'claude-v3.5-sonnet-v2',
            label: t('model.sonnet3-5-v2.label'),
            description: t('model.sonnet3-5-v2.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude35SonnetV2'
          },
          {
            modelId: 'claude-v3-opus',
            label: t('model.opus3.label'),
            description: t('model.opus3.description'),
            supportMediaType: CLAUDE_SUPPORTED_MEDIA_TYPES,
            modelActivateKey: 'claude3OpusV1'
          },
        ]
      : [
          {
            modelId: 'mistral-7b-instruct',
            label: t('model.mistral7b.label'),
            supportMediaType: [],
            modelActivateKey: 'mistral7b'
          },
          {
            modelId: 'mixtral-8x7b-instruct',
            label: t('model.mistral8x7b.label'),
            supportMediaType: [],
            modelActivateKey: 'mistral8x7b'
          },
          {
            modelId: 'mistral-large',
            label: t('model.mistralLarge.label'),
            supportMediaType: [],
            modelActivateKey: 'mistralLarge'
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
    } else if (modelActivate !== undefined) {
      const filtered = availableModels.filter(model => {
        const key = model.modelActivateKey as keyof ModelActivate;
        if (modelActivate) {
          return modelActivate[key] === true;
        } else {
          return true;
        }
      });
      setFilteredModels(filtered);
    }
  }, [modelActivate, availableModels]);

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
    const model = filteredModels.find(m => m.modelId === targetModelId);
    return model ? targetModelId : getDefaultModel();
  }, [filteredModels, getDefaultModel]);

  useEffect(() => {
    if (modelActivate === undefined) {return}

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
        const lastModelAvailable = filteredModels.some(m => m.modelId === recentUseModelId);
        if (!lastModelAvailable) {
          setModelId(selectModel(getDefaultModel()));
        }
      }
    }
  }, [botId, previousBotId, botModelId, recentUseModelId, modelId, filteredModels, setModelId, selectModel, getDefaultModel, modelActivate]);

  const model = useMemo(() => {
    return filteredModels.find((model) => model.modelId === modelId);
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
