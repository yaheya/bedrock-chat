import React from 'react';
import { useTranslation } from 'react-i18next';
import { BotMeta } from '../@types/bot';
import {
  PiArrowLeft,
  PiSealCheckFill,
  PiStar,
  PiStarFill,
} from 'react-icons/pi';
import ButtonIcon from './ButtonIcon';
import { useNavigate } from 'react-router-dom';
import useChat from '../hooks/useChat';
import Skeleton from './Skeleton';
import Button from './Button';
import { isPinnedBot } from '../utils/BotUtils';

type CardBotProps = {
  title: string;
  description: string;
  id?: string;
  isStarred?: boolean;
  isPinned?: boolean;
  onToggleStar?: (id: string, starred: boolean) => void;
};

export const CardBot: React.FC<CardBotProps> = (props) => {
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
        <div className="absolute right-1 top-1">
          <ButtonIcon onClick={handleStarClick}>
            {props.isStarred ? (
              <PiStarFill className="text-aws-aqua" />
            ) : (
              <PiStar />
            )}
          </ButtonIcon>
        </div>
      )}
      <div className="flex items-center">
        <div className="text-base font-bold">{props.title}</div>
        {props.isPinned && <PiSealCheckFill className="ml-1 text-aws-aqua" />}
      </div>
      <div className="text-sm italic text-dark-gray">
        {props.description === ''
          ? t('bot.label.noDescription')
          : props.description}
      </div>
    </div>
  );
};

export const SkeletonBot: React.FC = () => {
  return <Skeleton className="h-16 w-full rounded-xl" />;
};

type BotSearchResultsProps = {
  results: BotMeta[];
  isSearching: boolean;
  hasSearched: boolean;
  searchQuery: string;
  onToggleStar: (botId: string, starred: boolean) => void;
  onBackToHome: () => void; // Handler for returning to home view
};

const BotSearchResults: React.FC<BotSearchResultsProps> = ({
  results,
  isSearching,
  hasSearched,
  searchQuery,
  onToggleStar,
  onBackToHome,
}) => {
  const { t } = useTranslation();

  if (isSearching) {
    return (
      <div className="mt-6">
        <div className="text-2xl font-bold">
          {t('discover.search.searching')}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-6">
          <SkeletonBot />
          <SkeletonBot />
          <SkeletonBot />
          <SkeletonBot />
        </div>
        <div className="mt-4">
          <Button
            outlined
            onClick={onBackToHome}
            className="flex items-center gap-2">
            <PiArrowLeft /> {t('discover.search.backToHome')}
          </Button>
        </div>
      </div>
    );
  }

  if (hasSearched && results.length === 0) {
    return (
      <div className="mt-6">
        <div className="text-2xl font-bold">
          {t('discover.search.noResults', { query: searchQuery })}
        </div>
        <div className="mt-1 text-sm text-gray">
          {t('discover.search.tryDifferent')}
        </div>
        <div className="mt-4">
          <Button
            outlined
            onClick={onBackToHome}
            className="flex items-center gap-2">
            <PiArrowLeft /> {t('discover.search.backToHome')}
          </Button>
        </div>
      </div>
    );
  }

  if (hasSearched && results.length > 0) {
    return (
      <div className="mt-6">
        <div className="text-2xl font-bold">
          {t('discover.search.results', {
            count: results.length,
            query: searchQuery,
          })}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-6">
          {results.map((bot) => (
            <CardBot
              key={bot.id}
              title={bot.title}
              description={bot.description}
              id={bot.id}
              isStarred={bot.isStarred}
              isPinned={isPinnedBot(bot.sharedStatus)}
              onToggleStar={onToggleStar}
            />
          ))}
        </div>
        <div className="mt-4">
          <Button
            outlined
            onClick={onBackToHome}
            className="flex items-center gap-2">
            <PiArrowLeft /> {t('discover.search.backToHome')}
          </Button>
        </div>
      </div>
    );
  }

  return null;
};

export default BotSearchResults;
