import { BotMeta } from '../@types/bot';
import copy from 'copy-to-clipboard';

export const getBotUrl = (botId: string) => {
  return `${window.location.origin}/bot/${botId}`;
};

export const copyBotUrl = (botId: string) => {
  copy(getBotUrl(botId));
};

/**
 * ボットが管理者認定されているかどうかを判定する
 * @param bot ボットメタデータ
 * @returns 管理者認定されている場合はtrue、そうでない場合はfalse
 */
export const isPinnedBot = (bot: BotMeta): boolean => {
  return bot.sharedStatus.startsWith('pinned@');
};

/**
 * 管理者認定されているボットの順序を取得する
 * @param bot ボットメタデータ
 * @returns 管理者認定の順序（数値）。認定されていない場合は-1
 */
export const getPinOrder = (bot: BotMeta): number => {
  if (!isPinnedBot(bot)) {
    return -1;
  }

  const orderStr = bot.sharedStatus.split('@')[1];
  return parseInt(orderStr, 10);
};
/**
 * ボットが管理者認定可能かどうかを判定する
 * @param bot ボットメタデータ
 * @returns 管理者認定可能な場合はtrue、そうでない場合はfalse
 */
export const canBePinned = (bot: BotMeta): boolean => {
  return bot.sharedScope === 'all';
};
