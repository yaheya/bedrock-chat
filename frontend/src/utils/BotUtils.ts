import { BotMeta } from '../@types/bot';
import copy from 'copy-to-clipboard';

export const getBotUrl = (botId: string) => {
  return `${window.location.origin}/bot/${botId}`;
};

export const copyBotUrl = (botId: string) => {
  copy(getBotUrl(botId));
};

/**
 * Determines if a bot is pinned by an administrator
 * @param bot Bot metadata
 * @returns true if the bot is pinned, false otherwise
 */
export const isPinnedBot = (bot: BotMeta): boolean => {
  return bot.sharedStatus.startsWith('pinned@');
};

/**
 * Gets the order of a pinned bot
 * @param bot Bot metadata
 * @returns The numerical order of the pinned bot. Returns -1 if the bot is not pinned
 */
export const getPinOrder = (bot: BotMeta): number => {
  if (!isPinnedBot(bot)) {
    return -1;
  }

  const orderStr = bot.sharedStatus.split('@')[1];
  return parseInt(orderStr, 10);
};
/**
 * Determines if a bot can be pinned by an administrator
 * @param bot Bot metadata
 * @returns true if the bot can be pinned, false otherwise
 */
export const canBePinned = (bot: BotMeta): boolean => {
  return bot.sharedScope === 'all';
};
