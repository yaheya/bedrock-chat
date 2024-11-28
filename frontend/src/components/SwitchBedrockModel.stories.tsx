import SwitchBedrockModel from './SwitchBedrockModel';
import { MODEL_KEYS } from '../constants'
import { ModelActivate } from '../@types/bot';

export const Ideal = () => <SwitchBedrockModel modelActivate={Object.fromEntries(
  MODEL_KEYS.map(key => [key, true])
) as ModelActivate
}/>;
