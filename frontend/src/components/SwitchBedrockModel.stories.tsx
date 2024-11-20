import SwitchBedrockModel from './SwitchBedrockModel';

export const Ideal = () => <SwitchBedrockModel modelActivate={{
  claude3SonnetV1: true,
  claude3HaikuV1: true,
  claude35SonnetV1: true,
  claude35SonnetV2: true,
  claude35HaikuV1: true,
  claude3OpusV1: true,
}}/>;
