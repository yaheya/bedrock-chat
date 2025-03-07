import React, { useCallback, useMemo, useState } from 'react';
import { BaseProps } from '../@types/common';
import Button from './Button';
import ModalDialog from './ModalDialog';
import { Trans, useTranslation } from 'react-i18next';
import { SharedScope } from '../@types/bot';
import Toggle from './Toggle';
import { copyBotUrl, getBotUrl } from '../utils/BotUtils';
import RadioButton from './RadioButton';
import InputText from './InputText';
import { PiMagnifyingGlass, PiSpinner } from 'react-icons/pi';
import DialogShareBotPermission from './DialogShareBotPermission';
import i18n from 'i18next';

const getShareText = (userCount: number, groupCount: number): string => {
  // both zero
  if (userCount === 0 && groupCount === 0) {
    return i18n.t('bot.shareDialog.label.sharing.not_shared');
  }

  // both
  if (userCount > 0 && groupCount > 0) {
    if (userCount > 1 && groupCount > 1) {
      return i18n.t('bot.shareDialog.label.sharing.shared_both', {
        userCount,
        groupCount,
      });
    } else if (userCount > 1) {
      return i18n.t('bot.shareDialog.label.sharing.shared_both_user_plural', {
        userCount,
        groupCount,
      });
    } else if (groupCount > 1) {
      return i18n.t('bot.shareDialog.label.sharing.shared_both_group_plural', {
        userCount,
        groupCount,
      });
    } else {
      return i18n.t('bot.shareDialog.label.sharing.shared_both', {
        userCount,
        groupCount,
      });
    }
  }
  // only users
  if (userCount > 0) {
    return i18n.t('bot.shareDialog.label.sharing.shared_only_users', {
      count: userCount,
    });
  }

  // only groups
  return i18n.t('bot.shareDialog.label.sharing.shared_only_groups', {
    count: groupCount,
  });
};

type Props = BaseProps & {
  isOpen: boolean;
  isLoading?: boolean;
  botId?: string;
  sharedScope?: SharedScope;
  allowedUserIds?: string[];
  allowedGroupIds?: string[];
  onChangeSharedScope: (sharedScope: SharedScope) => void;
  onUpdateAllowedUserAndGroup: (
    allowedUserIds: string[],
    allowedGroupIds: string[]
  ) => void;
  onClose: () => void;
};

const DialogShareBot: React.FC<Props> = (props) => {
  const { t } = useTranslation();

  const [labelCopy, setLabelCopy] = useState(t('bot.button.copy'));
  const [isPermissionManagement, setIsPermissionManagement] = useState(false);
  const [searchUsersPrefix, setSearchUsersPrefix] = useState('');

  const isShared = useMemo(() => {
    return props.sharedScope ? props.sharedScope !== 'private' : false;
  }, [props.sharedScope]);

  const url = useMemo(() => {
    return getBotUrl(props.botId ?? '');
  }, [props.botId]);

  const onClickCopy = useCallback(() => {
    copyBotUrl(props.botId ?? '');
    setLabelCopy(t('bot.button.copied'));

    setTimeout(() => {
      setLabelCopy(t('bot.button.copy'));
    }, 3000);
  }, [props.botId, t]);

  return (
    <ModalDialog
      {...props}
      title={
        isPermissionManagement
          ? t('bot.shareDialog.label.memberManagement')
          : t('bot.shareDialog.title')
      }>
      {isPermissionManagement && (
        <DialogShareBotPermission
          allowedGroupIds={props.allowedGroupIds ?? []}
          allowedUserIds={props.allowedUserIds ?? []}
          searchUsersPrefix={searchUsersPrefix}
          onChangeSearchUsersPrefix={setSearchUsersPrefix}
          onUpdateAllowedUserAndGroup={(userIds, groupIds) => {
            props.onUpdateAllowedUserAndGroup(userIds, groupIds);
            setIsPermissionManagement(false);
          }}
          onCancel={() => {
            setSearchUsersPrefix('');
            setIsPermissionManagement(false);
          }}
        />
      )}
      {props.isLoading && (
        <div className="flex h-32 items-center justify-center">
          <PiSpinner className="animate-spin text-6xl" />
        </div>
      )}

      {!isPermissionManagement && !props.isLoading && (
        <>
          <div className="flex w-full items-center">
            <div className="w-full">{t('bot.shareDialog.switchLabel')}</div>

            <Toggle
              value={isShared}
              onChange={() => {
                props.onChangeSharedScope(isShared ? 'private' : 'all');
              }}
            />
          </div>

          {isShared && (
            <>
              <div className="-mb-1">Share with</div>
              <div className="flex gap-3">
                <RadioButton
                  name="shared-scope"
                  label={t('bot.shareDialog.label.all')}
                  checked={props.sharedScope === 'all'}
                  value=""
                  onChange={() => {
                    props.onChangeSharedScope('all');
                  }}
                />
                <RadioButton
                  name="shared-scope"
                  label={t('bot.shareDialog.label.partial')}
                  checked={props.sharedScope === 'partial'}
                  value=""
                  onChange={() => {
                    props.onChangeSharedScope('partial');
                  }}
                />
              </div>
            </>
          )}

          {props.sharedScope === 'partial' && (
            <>
              <div className="flex flex-col gap-1">
                <InputText
                  value={searchUsersPrefix}
                  placeholder={t('bot.shareDialog.label.search')}
                  icon={<PiMagnifyingGlass />}
                  onChange={(s) => {
                    setSearchUsersPrefix(s);
                    setIsPermissionManagement(true);
                  }}
                />
              </div>

              <div className="my-3 flex items-center justify-between">
                <div className="font-bold">
                  {getShareText(
                    props.allowedUserIds?.length ?? 0,
                    props.allowedGroupIds?.length ?? 0
                  )}
                </div>
                <Button
                  outlined
                  onClick={() => {
                    setIsPermissionManagement(true);
                  }}>
                  {t('bot.shareDialog.button.manage')}
                </Button>
              </div>
            </>
          )}

          <div className="my-3 flex w-full items-center text-xs">
            <div className="w-full">
              {props.sharedScope === 'private' ? (
                t('bot.shareDialog.off.content')
              ) : (
                <Trans
                  i18nKey="bot.shareDialog.on.content"
                  components={{
                    Link: (
                      <a
                        href="/bot/store"
                        className="italic text-aws-sea-blue underline"
                      />
                    ),
                  }}
                />
              )}
            </div>
          </div>

          {isShared && (
            <>
              <div className="text-xs">
                {t('bot.shareDialog.on.linkDescription')}
              </div>
              <div className="mt-1 flex justify-between rounded border border-aws-squid-ink/50 bg-aws-paper">
                <input
                  type="text"
                  className="my-2 ml-2 w-full bg-aws-paper"
                  readOnly
                  value={url}
                />
                <Button
                  outlined
                  className="rounded-none rounded-r border-0 border-l bg-white"
                  onClick={onClickCopy}>
                  {labelCopy}
                </Button>
              </div>
            </>
          )}
          <div className="mt-6 flex justify-end gap-2">
            <Button onClick={props.onClose} className="p-2">
              {t('button.done')}
            </Button>
          </div>
        </>
      )}
    </ModalDialog>
  );
};

export default DialogShareBot;
