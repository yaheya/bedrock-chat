import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { BaseProps } from '../@types/common';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import useDrawer from '../hooks/useDrawer';
import ButtonIcon from './ButtonIcon';
import {
  PiArrowRight,
  PiChat,
  PiCheck,
  PiCompass,
  PiListBullets,
  PiNotePencil,
  PiPencilLine,
  PiPresentationChart,
  PiRobot,
  PiTrash,
  PiX,
} from 'react-icons/pi';
import LazyOutputText from './LazyOutputText';
import { ConversationMeta } from '../@types/conversation';
import { BotListItem } from '../@types/bot';
import { isMobile } from 'react-device-detect';
import useChat from '../hooks/useChat';
import { useTranslation } from 'react-i18next';
import Menu from './Menu';
import DrawerItem from './DrawerItem';
import ExpandableDrawerGroup from './ExpandableDrawerGroup';
import { usePageLabel } from '../routes';
import { twMerge } from 'tailwind-merge';
import Button from './Button';
import Skeleton from './Skeleton';

type Props = BaseProps & {
  isAdmin: boolean;
  conversations?: ConversationMeta[];
  starredBots?: BotListItem[];
  recentlyUsedUnstarredBots?: BotListItem[];
  updateConversationTitle: (
    conversationId: string,
    title: string
  ) => Promise<void>;
  onSignOut: () => void;
  onDeleteConversation: (conversation: ConversationMeta) => void;
  onClearConversations: () => void;
  onSelectLanguage: () => void;
};

type ItemProps = BaseProps & {
  label: string;
  conversationId: string;
  generatedTitle?: boolean;
  updateTitle: (conversationId: string, title: string) => Promise<void>;
  onClick: () => void;
  onDelete: () => void;
};

const Item: React.FC<ItemProps> = (props) => {
  const { pathname } = useLocation();
  const { conversationId: pathParam } = useParams();
  const { conversationId } = useChat();
  const [tempLabel, setTempLabel] = useState('');
  const [editing, setEditing] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  const active = useMemo<boolean>(() => {
    return (
      pathParam === props.conversationId ||
      ((pathname === '/' || pathname.startsWith('/bot/')) &&
        conversationId == props.conversationId)
    );
  }, [conversationId, pathParam, pathname, props.conversationId]);

  const onClickEdit = useCallback(() => {
    setEditing(true);
    setTempLabel(props.label);
  }, [props.label]);

  const onClickUpdate = useCallback(() => {
    props.updateTitle(props.conversationId, tempLabel).then(() => {
      setEditing(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tempLabel, props.conversationId, props.updateTitle]);

  const onClickDelete = useCallback(() => {
    props.onDelete();
  }, [props]);

  useLayoutEffect(() => {
    if (editing) {
      inputRef.current?.focus();
    }
  }, [editing]);

  useLayoutEffect(() => {
    if (editing) {
      const listener = (e: DocumentEventMap['keypress']) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();

          // dispatch 処理の中で Title の更新を行う（同期を取るため）
          setTempLabel((newLabel) => {
            props.updateTitle(props.conversationId, newLabel).then(() => {
              setEditing(false);
            });
            return newLabel;
          });
        }
      };
      inputRef.current?.addEventListener('keypress', listener);

      inputRef.current?.focus();

      return () => {
        // eslint-disable-next-line react-hooks/exhaustive-deps
        inputRef.current?.removeEventListener('keypress', listener);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing]);

  return (
    <DrawerItem
      isActive={active}
      isBlur={!editing}
      to={`/${props.conversationId}`}
      onClick={props.onClick}
      icon={<PiChat />}
      labelComponent={
        <>
          {editing ? (
            <input
              ref={inputRef}
              type="text"
              className="w-full bg-transparent"
              value={tempLabel}
              onChange={(e) => {
                setTempLabel(e.target.value);
              }}
            />
          ) : (
            <>
              {props.generatedTitle ? (
                <LazyOutputText text={props.label} />
              ) : (
                <>{props.label}</>
              )}
            </>
          )}
        </>
      }
      actionComponent={
        <>
          {active && !editing && (
            <>
              <ButtonIcon className="text-base" onClick={onClickEdit}>
                <PiPencilLine />
              </ButtonIcon>

              <ButtonIcon className="text-base" onClick={onClickDelete}>
                <PiTrash />
              </ButtonIcon>
            </>
          )}
          {editing && (
            <>
              <ButtonIcon className="text-base" onClick={onClickUpdate}>
                <PiCheck />
              </ButtonIcon>

              <ButtonIcon
                className="text-base"
                onClick={() => {
                  setEditing(false);
                }}>
                <PiX />
              </ButtonIcon>
            </>
          )}
        </>
      }
    />
  );
};

const Drawer: React.FC<Props> = (props) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { getPageLabel } = usePageLabel();
  const { opened, switchOpen } = useDrawer();
  const { conversations, starredBots, recentlyUsedUnstarredBots } = props;

  const [prevConversations, setPrevConversations] =
    useState<typeof conversations>();
  const [generateTitleIndex, setGenerateTitleIndex] = useState(-1);

  const { newChat, conversationId } = useChat();
  const { botId } = useParams();

  useEffect(() => {
    setPrevConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    // 新規チャットの場合はTitleをLazy表示にする
    if (!conversations || !prevConversations) {
      return;
    }
    if (conversations.length > prevConversations?.length) {
      setGenerateTitleIndex(
        conversations?.findIndex(
          (c) =>
            (prevConversations?.findIndex((pc) => c.id === pc.id) ?? -1) < 0
        ) ?? -1
      );
    }
  }, [conversations, prevConversations]);

  const onClickNewChat = useCallback(() => {
    newChat();
    closeSmallDrawer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onClickNewBotChat = useCallback(
    () => {
      newChat();
      closeSmallDrawer();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const smallDrawer = useRef<HTMLDivElement>(null);

  const closeSmallDrawer = useCallback(() => {
    if (smallDrawer.current?.classList.contains('visible')) {
      switchOpen();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useLayoutEffect(() => {
    // リサイズイベントを拾って状態を更新する
    const onResize = () => {
      if (isMobile) {
        return;
      }

      // 狭い画面のDrawerが表示されていて、画面サイズが大きくなったら状態を更新
      if (!smallDrawer.current?.checkVisibility() && opened) {
        switchOpen();
      }
    };
    onResize();

    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened]);

  return (
    <>
      <div className="relative h-full overflow-y-auto bg-aws-squid-ink-light scrollbar-thin scrollbar-track-white scrollbar-thumb-aws-squid-ink-light/30 dark:bg-aws-ui-color-dark dark:scrollbar-thumb-aws-ui-color-dark/30">
        <nav
          className={`lg:visible lg:w-64 ${
            opened ? 'visible w-64' : 'invisible w-0'
          } text-sm  text-white transition-width`}>
          <div className="h-32 bg-aws-squid-ink-light dark:bg-aws-squid-ink-dark">
            <DrawerItem
              isActive={false}
              icon={<PiNotePencil />}
              to="/"
              onClick={onClickNewChat}
              labelComponent={t('button.newChat')}
            />
            <DrawerItem
              isActive={false}
              icon={<PiListBullets />}
              to="/bot/my"
              labelComponent={getPageLabel('/bot/my')}
              onClick={closeSmallDrawer}
            />
            <DrawerItem
              isActive={false}
              icon={<PiCompass />}
              to="/bot/discover"
              labelComponent={getPageLabel('/bot/discover')}
              onClick={closeSmallDrawer}
            />
          </div>

          <ExpandableDrawerGroup
            label={t('app.starredBots')}
            className="border-t bg-aws-squid-ink-light pt-1 dark:bg-aws-squid-ink-dark">
            {starredBots?.map((bot) => (
              <DrawerItem
                key={bot.id}
                isActive={botId === bot.id && !conversationId}
                to={`/bot/${bot.id}`}
                icon={<PiRobot />}
                labelComponent={bot.title}
                onClick={onClickNewBotChat}
              />
            ))}
          </ExpandableDrawerGroup>

          <ExpandableDrawerGroup
            label={t('app.recentlyUsedBots')}
            className="border-t bg-aws-squid-ink-light pt-1 dark:bg-aws-squid-ink-dark ">
            {recentlyUsedUnstarredBots === undefined && (
              <div className="flex flex-col gap-2 p-2">
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
              </div>
            )}
            {recentlyUsedUnstarredBots
              ?.slice(0, 15)
              .map((bot) => (
                <DrawerItem
                  key={bot.id}
                  isActive={false}
                  to={`/bot/${bot.id}`}
                  icon={<PiRobot />}
                  labelComponent={bot.title}
                  onClick={onClickNewBotChat}
                />
              ))}

            {recentlyUsedUnstarredBots && (
              <Button
                text
                rightIcon={<PiArrowRight />}
                className="w-full"
                onClick={() => {
                  navigate('/bot/recently-used');
                  closeSmallDrawer();
                }}>
                {t('bot.button.viewAll')}
              </Button>
            )}
          </ExpandableDrawerGroup>

          <ExpandableDrawerGroup
            label={t('app.conversationHistory')}
            className="border-t bg-aws-squid-ink-light pt-1 dark:bg-aws-squid-ink-dark">
            {conversations === undefined && (
              <div className="flex flex-col gap-2 p-2">
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
                <Skeleton className="h-10 w-full bg-aws-sea-blue-light/50 dark:bg-aws-sea-blue-dark/50" />
              </div>
            )}
            {conversations
              ?.slice(0, 5)
              .map((conversation, idx) => (
                <Item
                  key={idx}
                  className="grow"
                  label={conversation.title}
                  conversationId={conversation.id}
                  generatedTitle={idx === generateTitleIndex}
                  updateTitle={props.updateConversationTitle}
                  onClick={closeSmallDrawer}
                  onDelete={() => props.onDeleteConversation(conversation)}
                />
              ))}

            {conversations && (
              <Button
                text
                rightIcon={<PiArrowRight />}
                className="w-full"
                onClick={() => {
                  navigate('/conversations');
                  closeSmallDrawer();
                }}>
                {t('bot.button.viewAll')}
              </Button>
            )}
          </ExpandableDrawerGroup>

          <div
            className={twMerge(
              opened ? 'w-64' : 'w-0',
              props.isAdmin ? 'h-20' : 'h-10',
              'sticky bottom-0 z-50 mb-2 flex flex-col items-start border-t bg-aws-squid-ink-light transition-width dark:bg-aws-ui-color-dark lg:w-64'
            )}>
            {props.isAdmin && (
              <DrawerItem
                className="w-60"
                isActive={false}
                icon={<PiPresentationChart />}
                to="/admin/shared-bot-analytics"
                labelComponent={t('app.adminConsoles')}
                onClick={closeSmallDrawer}
              />
            )}
            <Menu
              className="mx-2 flex h-10 w-60 justify-start"
              onSignOut={props.onSignOut}
              onSelectLanguage={props.onSelectLanguage}
              onClearConversations={props.onClearConversations}
            />
          </div>
        </nav>
      </div>

      <div
        ref={smallDrawer}
        className={`lg:hidden ${opened ? 'visible' : 'hidden'}`}>
        <ButtonIcon
          className="fixed left-64 top-0 z-50 text-white"
          onClick={switchOpen}>
          <PiX />
        </ButtonIcon>
        <div
          className="fixed z-40 h-dvh w-screen bg-dark-gray/90"
          onClick={switchOpen}></div>
      </div>
    </>
  );
};

export default Drawer;
