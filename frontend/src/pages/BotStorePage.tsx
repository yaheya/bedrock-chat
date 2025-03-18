import React, { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  PiBinoculars,
  PiCertificate,
  PiMagnifyingGlass,
  PiRanking,
  PiStar,
  PiStarFill,
} from 'react-icons/pi';
import InputText from '../components/InputText';
import useBotStore from '../hooks/useBotStore';
import Skeleton from '../components/Skeleton';
import { twMerge } from 'tailwind-merge';
import { useNavigate } from 'react-router-dom';
import useChat from '../hooks/useChat';
import ButtonIcon from '../components/ButtonIcon';
import useBot from '../hooks/useBot';

type CardBotProps = {
  title: string;
  description: string;
  id?: string;
  isStarred?: boolean;
  onToggleStar?: (id: string, starred: boolean) => void;
};

const CardBot: React.FC<CardBotProps> = (props) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { newChat } = useChat();

  const handleClick = () => {
    if (props.id) {
      newChat();
      navigate(`/bot/${props.id}`);
    }
  };

  const handleStarClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (props.id && props.onToggleStar) {
      props.onToggleStar(props.id, !props.isStarred);
    }
  };

  return (
    <div
      className="relative cursor-pointer rounded-xl border border-gray bg-white px-4 py-2 transition-colors hover:bg-light-gray"
      onClick={handleClick}>
      {props.id && props.onToggleStar && (
        <div className="absolute right-2 top-2">
          <ButtonIcon onClick={handleStarClick}>
            {props.isStarred ? (
              <PiStarFill className="text-aws-aqua" />
            ) : (
              <PiStar />
            )}
          </ButtonIcon>
        </div>
      )}
      <div className="pr-8 text-base font-bold">{props.title}</div>
      <div className="text-sm italic text-dark-gray">
        {props.description === ''
          ? t('bot.label.noDescription')
          : props.description}
      </div>
    </div>
  );
};

const SkeletonBot: React.FC = () => {
  return <Skeleton className="h-16 w-full rounded-xl" />;
};

const BotStorePage: React.FC = () => {
  const { t } = useTranslation();

  const {
    pickupBots,
    isLoadingPickupBots,
    popularBots,
    isLoadingPopularBots,
    pinnedBots,
    toggleBotStarred,
  } = useBotStore();
  const { mutateStarredBots } = useBot();

  const handleToggleStar = useCallback(
    (botId: string, starred: boolean) => {
      toggleBotStarred(botId, starred).finally(() => {
        mutateStarredBots();
      });
    },
    [mutateStarredBots, toggleBotStarred]
  );

  return (
    <>
      <div className="mb-32 flex h-full justify-center">
        <div className="flex w-full max-w-screen-xl flex-col gap-3 px-4 pt-8 lg:w-4/5">
          <div className="flex justify-center text-4xl font-bold">
            {t('store.pageTitle')}
          </div>

          <div className=" flex w-full flex-col items-center justify-center text-dark-gray">
            <div>{t('store.description')}</div>
          </div>

          <div className="mt-6">
            <InputText
              icon={<PiMagnifyingGlass />}
              placeholder={t('store.search.placeholder')}
              value=""
            />
          </div>

          <div
            className={twMerge(
              pinnedBots.length === 0 ? 'invisible h-0 scale-y-0' : 'mt-6',
              'transition-all duration-300'
            )}>
            <div className="flex items-center text-2xl font-bold">
              <PiCertificate className="mr-2" />
              {t('store.essential.label')}
            </div>
            <div className="mt-1 text-sm text-gray">
              {t('store.essential.description')}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-6">
              {pinnedBots.map((bot) => (
                <CardBot
                  key={bot.id}
                  title={bot.title}
                  description={bot.description}
                  id={bot.id}
                  isStarred={bot.isStarred}
                  onToggleStar={handleToggleStar}
                />
              ))}
            </div>
          </div>

          <div className="mt-6">
            <div className="flex items-center text-2xl font-bold">
              <PiRanking className="mr-2" />
              {t('store.trending.label')}
            </div>
            <div className="mt-1 text-sm text-gray">
              {t('store.trending.description')}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-9">
              {isLoadingPopularBots && (
                <>
                  <SkeletonBot />
                  <SkeletonBot />
                </>
              )}
              {popularBots.map((bot, idx) => (
                <div className="flex" key={bot.id}>
                  <div className="mr-2 text-xl font-bold">{idx + 1}.</div>
                  <div className="grow">
                    <CardBot
                      title={bot.title}
                      description={bot.description}
                      id={bot.id}
                      isStarred={bot.isStarred}
                      onToggleStar={handleToggleStar}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <div className="flex items-center text-2xl font-bold">
              <PiBinoculars className="mr-2" />
              {t('store.discover.label')}
            </div>
            <div className="mt-1 text-sm text-gray">
              {t('store.discover.description')}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-6">
              {isLoadingPickupBots && (
                <>
                  <SkeletonBot />
                  <SkeletonBot />
                </>
              )}
              {pickupBots.map((bot) => (
                <CardBot
                  key={bot.id}
                  title={bot.title}
                  description={bot.description}
                  id={bot.id}
                  isStarred={bot.isStarred}
                  onToggleStar={handleToggleStar}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default BotStorePage;
