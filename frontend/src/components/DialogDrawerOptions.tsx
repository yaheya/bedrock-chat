import React, { useEffect, useState } from 'react';
import { BaseProps, DrawerOptions } from '../@types/common';
import Button from './Button';
import ModalDialog from './ModalDialog';
import { useTranslation } from 'react-i18next';
import InputText from './InputText';

type Props = BaseProps & {
  isOpen: boolean;
  drawerOptions: DrawerOptions;
  onChangeDrawerOptions: (drawerOptions: DrawerOptions) => void;
  onClose: () => void;
};

const DialogDrawerOptions: React.FC<Props> = (props) => {
  const { t } = useTranslation();

  const [starredBotsCount, setStarredBotsCount] = useState(0);
  const [recentlyUsedBotsCount, setRecentlyUsedBotsCount] = useState(0);
  const [conversationHistoryCount, setConversationHistoryCount] = useState(0);

  useEffect(() => {
    if (props.isOpen) {
      setStarredBotsCount(props.drawerOptions.displayCount.starredBots);
      setRecentlyUsedBotsCount(
        props.drawerOptions.displayCount.recentlyUsedBots
      );
      setConversationHistoryCount(
        props.drawerOptions.displayCount.conversationHistory
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.isOpen]);

  return (
    <ModalDialog {...props} title={t('drawerOptionsDialog.title')}>
      <div className="flex flex-col gap-3">
        <div>
          <div className="text-base font-bold">
            {t('drawerOptionsDialog.label.displayCount')}
          </div>
          <div className="ml-3 mt-1">
            <InputText
              label={t('app.starredBots')}
              type="number"
              value={starredBotsCount.toString()}
              onChange={(s) => {
                setStarredBotsCount(parseInt(s));
              }}
            />
            <InputText
              label={t('app.recentlyUsedBots')}
              type="number"
              value={recentlyUsedBotsCount.toString()}
              onChange={(s) => {
                setRecentlyUsedBotsCount(parseInt(s));
              }}
            />
            <InputText
              label={t('app.conversationHistory')}
              type="number"
              value={conversationHistoryCount.toString()}
              onChange={(s) => {
                setConversationHistoryCount(parseInt(s));
              }}
            />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <Button onClick={props.onClose} className="p-2" outlined>
          {t('button.cancel')}
        </Button>
        <Button
          onClick={() => {
            props.onChangeDrawerOptions({
              displayCount: {
                starredBots: starredBotsCount,
                recentlyUsedBots: recentlyUsedBotsCount,
                conversationHistory: conversationHistoryCount,
              },
            });
          }}
          className="p-2">
          {t('button.ok')}
        </Button>
      </div>
    </ModalDialog>
  );
};

export default DialogDrawerOptions;
