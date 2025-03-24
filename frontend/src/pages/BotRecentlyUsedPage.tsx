import React, { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PiStar, PiStarFill, PiTrash } from 'react-icons/pi';
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
import { isPinnedBot } from '../utils/BotUtils';
import { produce } from 'immer';

const BotRecentlyUsedPage: React.FC = () => {
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
  const {
    myBots,
    recentlyUsedSharedBots,
    recentlyUsedBots,
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
      <div className="flex h-full justify-center">
        <div className="w-full max-w-screen-xl px-4 lg:w-4/5">
          <div className="h-1/2 w-full pt-8">
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

export default BotRecentlyUsedPage;
