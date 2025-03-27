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
  PiTrashBold,
  PiUsers,
} from 'react-icons/pi';
import { useNavigate } from 'react-router-dom';
import useBot from '../hooks/useBot';
import { BotListItem, BotMeta } from '../@types/bot';
import DialogConfirmDeleteBot from '../components/DialogConfirmDeleteBot';
import DialogConfirmShareBot from '../components/DialogShareBot';
import ButtonIcon from '../components/ButtonIcon';
import PopoverMenu from '../components/PopoverMenu';
import PopoverItem from '../components/PopoverItem';
import useChat from '../hooks/useChat';
import StatusSyncBot from '../components/StatusSyncBot';
import useLoginUser from '../hooks/useLoginUser';
import ListItemBot from '../components/ListItemBot';
import PinnedBotIcon from '../components/PinnedBotIcon';
import useShareBot from '../hooks/useShareBot';
import useBotPinning from '../hooks/useBotPinning';
import { isPinnedBot, canBePinned } from '../utils/BotUtils';
import { produce } from 'immer';
import ListPageLayout from '../layouts/ListPageLayout';

const BotExplorePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAllowCreatingBot, isAllowApiSettings, isAdmin } = useLoginUser();
  const [isOpenDeleteDialog, setIsOpenDeleteDialog] = useState(false);
  const [isOpenShareDialog, setIsOpenShareDialog] = useState(false);
  const [targetDelete, setTargetDelete] = useState<BotMeta>();
  const [openedShareDialogBotId, setOpenedShareDialogBotId] = useState<
    string | undefined
  >();
  const { pinBot, unpinBot } = useBotPinning();

  const { newChat } = useChat();
  const { myBots, deleteMyBot, updateMyBotStarred, mutateMyBots } =
    useBot(true);

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

  const togglePinBot = useCallback(
    (bot: BotListItem) => {
      mutateMyBots(
        produce(myBots, (draft) => {
          if (draft) {
            const target = draft.find((b) => b.id === bot.id);
            if (target) {
              target.sharedStatus = isPinnedBot(bot.sharedStatus)
                ? 'shared'
                : 'pinned@000';
            }
          }
        }),
        {
          revalidate: false,
        }
      );

      isPinnedBot(bot.sharedStatus)
        ? unpinBot(bot.id).finally(() => {
            mutateMyBots();
          })
        : pinBot(bot.id, 0).finally(() => {
            mutateMyBots();
          });
    },
    [mutateMyBots, myBots, pinBot, unpinBot]
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
      <ListPageLayout
        pageTitle={t('bot.label.myBots')}
        pageTitleHelp={t('bot.help.overview')}
        pageTitleActions={
          <Button
            className="text-sm"
            disabled={!isAllowCreatingBot}
            outlined
            icon={<PiPlus />}
            onClick={onClickNewBot}>
            {t('bot.button.newBot')}
          </Button>
        }
        isEmpty={myBots?.length === 0}
        emptyMessage={t('bot.label.noBots')}>
        {myBots?.map((bot) => (
          <ListItemBot key={bot.id} bot={bot} onClick={onClickBot}>
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
                {bot.sharedScope === 'all' || bot.sharedScope === 'partial' ? (
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
                  {isAdmin && canBePinned(bot.sharedScope) && (
                    <PopoverItem
                      onClick={() => {
                        togglePinBot(bot);
                      }}>
                      {isPinnedBot(bot.sharedScope) ? (
                        <>
                          <PinnedBotIcon showAlways className="text-aws-aqua" />
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
      </ListPageLayout>
    </>
  );
};

export default BotExplorePage;
