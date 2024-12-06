import SwitchBedrockModel from './SwitchBedrockModel';
import { MODEL_KEYS } from '../constants';
import { ActiveModels } from '../@types/bot';

export const Ideal = () => (
  <SwitchBedrockModel
    activeModels={
      Object.fromEntries(MODEL_KEYS.map((key) => [key, true])) as ActiveModels
    }
  />
);
