import React from 'react';
import { PiSealCheck, PiSealCheckFill } from 'react-icons/pi';
import { BaseProps } from '../@types/common.d';
import { BotMeta } from '../@types/bot';
import { isPinnedBot } from '../utils/BotUtils';

type Props = BaseProps & {
  bot?: BotMeta;
  showAlways?: boolean;
  outlined?: boolean;
};

/**
 * Icon component that indicates a pinned bot
 * @param props.bot Bot metadata
 * @param props.className CSS class name to apply to the icon
 * @param props.showAlways If true, always show the icon regardless of whether the bot is pinned
 * @param props.outlined If true, show the outlined version of the icon
 */
const PinnedBotIcon: React.FC<Props> = ({
  bot,
  className = '',
  showAlways = false,
  outlined = false,
}) => {
  if (!bot && !showAlways) {
    return null;
  }
  if (bot && !isPinnedBot(bot) && !showAlways) {
    return null;
  }

  return outlined ? (
    <PiSealCheck className={className} />
  ) : (
    <PiSealCheckFill className={className} />
  );
};

export default PinnedBotIcon;
