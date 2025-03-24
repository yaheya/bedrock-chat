import React, { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  PiEraser,
  PiGlobe,
  PiLink,
  PiLockKey,
  PiPencil,
  PiStar,
  PiStarFill,
  PiTrashBold,
  PiUsers,
} from 'react-icons/pi';
import { useNavigate } from 'react-router-dom';
import useBot from '../hooks/useBot';
import { BotListItem, BotMeta } from '../@types/bot';
import DialogConfirmDeleteBot from '../components/DialogConfirmDeleteBot';
import DialogConfirmShareBot from '../components/DialogShareBot';
import ButtonIcon from '../components/ButtonIcon';
import useChat from '../hooks/useChat';
import useLoginUser from '../hooks/useLoginUser';
import ListItemBot from '../components/ListItemBot';
import useShareBot from '../hooks/useShareBot';
import useBotPinning from '../hooks/useBotPinning';
import { isPinnedBot, canBePinned } from '../utils/BotUtils';
import { produce } from 'immer';
import PopoverMenu from '../components/PopoverMenu';
import PopoverItem from '../components/PopoverItem';
import PinnedBotIcon from '../components/PinnedBotIcon';

const BotRecentlyUsedPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAllowApiSettings, isAdmin } = useLoginUser();
  const [isOpenDeleteDialog, setIsOpenDeleteDialog] = useState(false);
  const [isOpenShareDialog, setIsOpenShareDialog] = useState(false);
  const [targetDelete, setTargetDelete] = useState<BotMeta>();
  const [openedShareDialogBotId, setOpenedShareDialogBotId] = useState<
    string | undefined
  >();
  const { pinBot, unpinBot } = useBotPinning();

  const { newChat } = useChat();
  const {
    recentlyUsedBots,
    deleteMyBot,
    deleteRecentlyUsedBot,
    updateMyBotStarred,
    updateSharedBotStarred,
    mutateRecentlyUsedBots,
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
    myBots: recentlyUsedBots ?? [],
    mutateMyBots: mutateRecentlyUsedBots,
  });

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

  const onClickBot = useCallback(
    (botId: string) => {
      newChat();
      navigate(`/bot/${botId}`);
    },
    [navigate, newChat]
  );

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

  const togglePinBot = useCallback(
    (bot: BotListItem) => {
      mutateRecentlyUsedBots(
        produce(recentlyUsedBots, (draft) => {
          if (draft) {
            const target = draft.find((b) => b.id === bot.id);
            if (target) {
              target.sharedStatus = isPinnedBot(bot) ? 'shared' : 'pinned@000';
            }
          }
        }),
        {
          revalidate: false,
        }
      );

      isPinnedBot(bot)
        ? unpinBot(bot.id).finally(() => {
            mutateRecentlyUsedBots();
          })
        : pinBot(bot.id, 0).finally(() => {
            mutateRecentlyUsedBots();
          });
    },
    [mutateRecentlyUsedBots, pinBot, recentlyUsedBots, unpinBot]
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
          <div className="size-full pt-8">
            <div className="border-b border-gray pb-2 text-2xl font-bold">
              {t('bot.label.recentlyUsedBots')}
            </div>
            <div className="h-4/5 overflow-x-auto overflow-y-scroll border-gray pr-1 scrollbar-thin scrollbar-thumb-aws-font-color/20">
              <div className="h-full">
                {recentlyUsedBots?.length === 0 && (
                  <div className="flex size-full items-center justify-center italic text-dark-gray">
                    {t('bot.label.noBotsRecentlyUsed')}
                  </div>
                )}
                {recentlyUsedBots?.map((bot) => (
                  <ListItemBot key={bot.id} bot={bot} onClick={onClickBot}>
                    <div className="flex items-center">
                      {bot.owned && (
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
                      )}

                      <div className="mr-5">
                        {bot.isStarred ? (
                          <ButtonIcon
                            disabled={!bot.available}
                            onClick={() => {
                              // Optimistic update
                              const newIsStarred = false;
                              mutateRecentlyUsedBots(
                                produce(recentlyUsedBots, (draft) => {
                                  if (draft) {
                                    const target = draft.find(
                                      (b) => b.id === bot.id
                                    );
                                    if (target) {
                                      target.isStarred = newIsStarred;
                                    }
                                  }
                                }),
                                {
                                  revalidate: false,
                                }
                              );

                              // Actual API call
                              (bot.owned
                                ? updateMyBotStarred(bot.id, newIsStarred)
                                : updateSharedBotStarred(bot.id, newIsStarred)
                              ).finally(() => {
                                mutateRecentlyUsedBots();
                              });
                            }}>
                            <PiStarFill className="text-aws-aqua" />
                          </ButtonIcon>
                        ) : (
                          <ButtonIcon
                            disabled={!bot.available}
                            onClick={() => {
                              // Optimistic update
                              const newIsStarred = true;
                              mutateRecentlyUsedBots(
                                produce(recentlyUsedBots, (draft) => {
                                  if (draft) {
                                    const target = draft.find(
                                      (b) => b.id === bot.id
                                    );
                                    if (target) {
                                      target.isStarred = newIsStarred;
                                    }
                                  }
                                }),
                                {
                                  revalidate: false,
                                }
                              );

                              // Actual API call
                              (bot.owned
                                ? updateMyBotStarred(bot.id, newIsStarred)
                                : updateSharedBotStarred(bot.id, newIsStarred)
                              ).finally(() => {
                                mutateRecentlyUsedBots();
                              });
                            }}>
                            <PiStar />
                          </ButtonIcon>
                        )}
                      </div>
                      <div className="relative">
                        <PopoverMenu className="h-8" target="bottom-right">
                          {bot.owned && (
                            <>
                              <PopoverItem
                                onClick={() => {
                                  onClickEditBot(bot.id);
                                }}>
                                <PiPencil />
                                {t('bot.button.edit')}
                              </PopoverItem>
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
                              {isAdmin && canBePinned(bot) && (
                                <PopoverItem
                                  onClick={() => {
                                    togglePinBot(bot);
                                  }}>
                                  {isPinnedBot(bot) ? (
                                    <>
                                      <PinnedBotIcon
                                        showAlways
                                        className="text-aws-aqua"
                                      />
                                      {t('bot.button.unpinBot')}
                                    </>
                                  ) : (
                                    <>
                                      <PinnedBotIcon showAlways outlined />
                                      {t('bot.button.pinBot')}
                                    </>
                                  )}
                                </PopoverItem>
                              )}
                              <PopoverItem
                                onClick={() => {
                                  deleteRecentlyUsedBot(bot.id);
                                }}>
                                <PiEraser />
                                {t('bot.button.removeFromRecent')}
                              </PopoverItem>
                              <PopoverItem
                                className="font-bold text-red"
                                onClick={() => {
                                  onClickDelete(bot);
                                }}>
                                <PiTrashBold />
                                {t('bot.button.delete')}
                              </PopoverItem>
                            </>
                          )}
                          {!bot.owned && (
                            <>
                              {isAdmin && canBePinned(bot) && (
                                <PopoverItem
                                  onClick={() => {
                                    togglePinBot(bot);
                                  }}>
                                  {isPinnedBot(bot) ? (
                                    <>
                                      <PinnedBotIcon
                                        showAlways
                                        className="text-aws-aqua"
                                      />
                                      {t('bot.button.unpinBot')}
                                    </>
                                  ) : (
                                    <>
                                      <PinnedBotIcon showAlways outlined />
                                      {t('bot.button.pinBot')}
                                    </>
                                  )}
                                </PopoverItem>
                              )}
                              <PopoverItem
                                onClick={() => {
                                  deleteRecentlyUsedBot(bot.id);
                                }}>
                                <PiEraser />
                                {t('bot.button.removeFromRecent')}
                              </PopoverItem>
                            </>
                          )}
                        </PopoverMenu>
                      </div>
                    </div>
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

export default BotRecentlyUsedPage;
