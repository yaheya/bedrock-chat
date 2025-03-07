import React, { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '../components/Button';
import {
  PiGlobe,
  PiLink,
  PiLockKey,
  PiPlus,
  PiStar,
  PiStarFill,
  PiTrash,
  PiTrashBold,
  PiUsers,
} from 'react-icons/pi';
import { useNavigate } from 'react-router-dom';
import useBot from '../hooks/useBot';
import { BotMeta } from '../@types/bot';
import DialogConfirmDeleteBot from '../components/DialogConfirmDeleteBot';
import DialogConfirmShareBot from '../components/DialogShareBot';
import ButtonIcon from '../components/ButtonIcon';
import PopoverMenu from '../components/PopoverMenu';
import PopoverItem from '../components/PopoverItem';
import useChat from '../hooks/useChat';
import Help from '../components/Help';
import StatusSyncBot from '../components/StatusSyncBot';
import useLoginUser from '../hooks/useLoginUser';
import ListItemBot from '../components/ListItemBot';
import { TooltipDirection } from '../constants';
import useShareBot from '../hooks/useShareBot';

const BotExplorePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAllowCreatingBot, isAllowApiSettings } = useLoginUser();
  const [isOpenDeleteDialog, setIsOpenDeleteDialog] = useState(false);
  const [isOpenShareDialog, setIsOpenShareDialog] = useState(false);
  const [targetDelete, setTargetDelete] = useState<BotMeta>();
  const [openedShareDialogBotId, setOpenedShareDialogBotId] = useState<
    string | undefined
  >();

  const { newChat } = useChat();
  const {
    myBots,
    recentlyUsedSharedBots,
    deleteMyBot,
    deleteRecentlyUsedBot,
    updateMyBotStarred,
    updateSharedBotStarred,
    mutateMyBots,
  } = useBot(true);

  const {
    sharedScope,
    allowedGroupIds,
    allowedUserIds,
    isLoading: isLoadingShareBot,
    updateSharedScope,
    updateSharedUsersAndGroups,
  } = useShareBot({
    botId: openedShareDialogBotId,
    myBots: myBots ?? [],
    mutateMyBots,
  });

  const onClickNewBot = useCallback(() => {
    navigate('/bot/new');
  }, [navigate]);

  const onClickEditBot = useCallback(
    (botId: string) => {
      navigate(`/bot/edit/${botId}`);
    },
    [navigate]
  );

  const onClickDelete = useCallback((target: BotMeta) => {
    setIsOpenDeleteDialog(true);
    setTargetDelete(target);
  }, []);

  const onDeleteMyBot = useCallback(() => {
    if (targetDelete) {
      setIsOpenDeleteDialog(false);
      deleteMyBot(targetDelete.id).catch(() => {
        setIsOpenDeleteDialog(true);
      });
    }
  }, [deleteMyBot, targetDelete]);

  const onClickShare = useCallback((botId: string) => {
    setIsOpenShareDialog(true);
    setOpenedShareDialogBotId(botId);
  }, []);

  const onClickApiSettings = useCallback(
    (botId: string) => {
      navigate(`/bot/api-settings/${botId}`);
    },
    [navigate]
  );

  const onClickBot = useCallback(
    (botId: string) => {
      newChat();
      navigate(`/bot/${botId}`);
    },
    [navigate, newChat]
  );

  return (
    <>
      <DialogConfirmDeleteBot
        isOpen={isOpenDeleteDialog}
        target={targetDelete}
        onDelete={onDeleteMyBot}
        onClose={() => {
          setIsOpenDeleteDialog(false);
        }}
      />
      <DialogConfirmShareBot
        isOpen={isOpenShareDialog}
        botId={openedShareDialogBotId}
        sharedScope={sharedScope}
        allowedGroupIds={allowedGroupIds}
        allowedUserIds={allowedUserIds}
        isLoading={isLoadingShareBot}
        onChangeSharedScope={(scope) => {
          updateSharedScope(scope);
        }}
        onUpdateAllowedUserAndGroup={(userIds, groupIds) => {
          updateSharedUsersAndGroups(userIds, groupIds);
        }}
        onClose={() => {
          setIsOpenShareDialog(false);
        }}
      />
      <div className="flex h-full justify-center">
        <div className="w-full max-w-screen-xl px-4 lg:w-4/5">
          <div className="h-1/2 w-full pt-8">
            <div className="flex items-end justify-between">
              <div className="flex items-center gap-2">
                <div className="text-xl font-bold">{t('bot.label.myBots')}</div>
                <Help
                  direction={TooltipDirection.RIGHT}
                  message={t('bot.help.overview')}
                />
              </div>

              <Button
                className="text-sm"
                disabled={!isAllowCreatingBot}
                outlined
                icon={<PiPlus />}
                onClick={onClickNewBot}>
                {t('bot.button.newBot')}
              </Button>
            </div>
            <div className="mt-2 border-b border-gray"></div>

            <div className="h-4/5 overflow-x-auto overflow-y-scroll border-b border-gray pr-1 scrollbar-thin scrollbar-thumb-aws-font-color/20">
              <div className="h-full min-w-[480px]">
                {myBots?.length === 0 && (
                  <div className="flex size-full items-center justify-center italic text-dark-gray">
                    {t('bot.label.noBots')}
                  </div>
                )}
                {myBots?.map((bot) => (
                  <ListItemBot
                    key={bot.id}
                    bot={bot}
                    onClick={onClickBot}
                    className="last:border-b-0">
                    <div className="flex items-center">
                      {bot.owned && (
                        <StatusSyncBot
                          className="mr-5"
                          syncStatus={bot.syncStatus}
                          onClickError={() => {
                            navigate(`/bot/edit/${bot.id}`);
                          }}
                        />
                      )}

                      <div className="mr-5 flex justify-end">
                        {bot.sharedScope === 'all' ||
                        bot.sharedScope === 'partial' ? (
                          <div className="flex items-center">
                            <PiUsers className="mr-1" />
                            <ButtonIcon
                              className="-mr-3"
                              onClick={() => {
                                onClickShare(bot.id);
                              }}>
                              <PiLink />
                            </ButtonIcon>
                          </div>
                        ) : (
                          <div className="ml-7">
                            <PiLockKey />
                          </div>
                        )}
                      </div>

                      <div className="mr-5">
                        {bot.isStarred ? (
                          <ButtonIcon
                            disabled={!bot.available}
                            onClick={() => {
                              updateMyBotStarred(bot.id, false);
                            }}>
                            <PiStarFill className="text-aws-aqua" />
                          </ButtonIcon>
                        ) : (
                          <ButtonIcon
                            disabled={!bot.available}
                            onClick={() => {
                              updateMyBotStarred(bot.id, true);
                            }}>
                            <PiStar />
                          </ButtonIcon>
                        )}
                      </div>

                      <Button
                        className="mr-2 h-8 text-sm font-semibold"
                        outlined
                        onClick={() => {
                          onClickEditBot(bot.id);
                        }}>
                        {t('bot.button.edit')}
                      </Button>
                      <div className="relative">
                        <PopoverMenu className="h-8" target="bottom-right">
                          <PopoverItem
                            onClick={() => {
                              onClickShare(bot.id);
                            }}>
                            <PiUsers />
                            {t('bot.button.share')}
                          </PopoverItem>
                          {isAllowApiSettings && (
                            <PopoverItem
                              onClick={() => {
                                onClickApiSettings(bot.id);
                              }}>
                              <PiGlobe />
                              {t('bot.button.apiSettings')}
                            </PopoverItem>
                          )}
                          <PopoverItem
                            className="font-bold text-red"
                            onClick={() => {
                              onClickDelete(bot);
                            }}>
                            <PiTrashBold />
                            {t('bot.button.delete')}
                          </PopoverItem>
                        </PopoverMenu>
                      </div>
                    </div>
                  </ListItemBot>
                ))}
              </div>
            </div>
          </div>
          <div className="h-1/2 w-full">
            <div className="text-xl font-bold">
              {t('bot.label.recentlyUsedBots')}
            </div>
            <div className="mt-2 border-b border-gray"></div>
            <div className="h-4/5 overflow-x-auto overflow-y-scroll border-b border-gray pr-1 scrollbar-thin scrollbar-thumb-aws-font-color/20">
              <div className="h-full min-w-[480px]">
                {recentlyUsedSharedBots?.length === 0 && (
                  <div className="flex size-full items-center justify-center italic text-dark-gray">
                    {t('bot.label.noBotsRecentlyUsed')}
                  </div>
                )}
                {recentlyUsedSharedBots?.map((bot) => (
                  <ListItemBot
                    key={bot.id}
                    bot={bot}
                    onClick={onClickBot}
                    className="last:border-b-0">
                    {bot.isStarred ? (
                      <ButtonIcon
                        disabled={!bot.available}
                        onClick={() => {
                          updateSharedBotStarred(bot.id, false);
                        }}>
                        <PiStarFill className="text-aws-aqua" />
                      </ButtonIcon>
                    ) : (
                      <ButtonIcon
                        disabled={!bot.available}
                        onClick={() => {
                          updateSharedBotStarred(bot.id, true);
                        }}>
                        <PiStar />
                      </ButtonIcon>
                    )}
                    <ButtonIcon
                      className="text-red"
                      onClick={() => {
                        deleteRecentlyUsedBot(bot.id);
                      }}>
                      <PiTrash />
                    </ButtonIcon>
                  </ListItemBot>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default BotExplorePage;
