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
 * ピン留めされたボットを示すアイコンコンポーネント
 * @param props.bot ボットメタデータ
 * @param props.className アイコンに適用するクラス名
 * @param props.showAlways ボットがピン留めされていなくても常に表示する場合はtrue
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
