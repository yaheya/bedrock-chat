import React from 'react';
import { useTranslation } from 'react-i18next';
import { BotMeta } from '../@types/bot';
import { PiArrowLeft } from 'react-icons/pi';
import { useNavigate } from 'react-router-dom';
import useChat from '../hooks/useChat';
import Skeleton from './Skeleton';
import Button from './Button';
import IconPinnedBot from './IconPinnedBot';

type CardBotProps = {
  title: string;
  description: string;
  id: string;
  sharedStatus: string;
};

export const CardBot: React.FC<CardBotProps> = (props) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { newChat } = useChat();

  const handleClick = () => {
    newChat();
    navigate(`/bot/${props.id}`);
  };

  return (
    <div
      className="relative flex h-28 w-full cursor-pointer flex-col rounded-xl border border-gray bg-white px-4 py-2 transition-colors hover:bg-light-gray dark:border-dark-gray dark:bg-aws-squid-ink-dark"
      onClick={handleClick}>
      <div className="flex items-center">
        <IconPinnedBot
          className="mr-1 shrink-0 text-aws-aqua"
          botSharedStatus={props.sharedStatus}
        />
        <div className="truncate text-base font-bold">{props.title}</div>
      </div>
      <div className="line-clamp-3 overflow-hidden text-sm italic text-dark-gray">
        {props.description === ''
          ? t('bot.label.noDescription')
          : props.description}
      </div>
    </div>
  );
};

export const SkeletonBot: React.FC = () => {
  return <Skeleton className="h-[120px] w-full rounded-xl" />;
};

type BotSearchResultsProps = {
  results: BotMeta[];
  isSearching: boolean;
  hasSearched: boolean;
  searchQuery: string;
  onBackToHome: () => void; // Handler for returning to home view
};

const BotSearchResults: React.FC<BotSearchResultsProps> = ({
  results,
  isSearching,
  hasSearched,
  searchQuery,
  onBackToHome,
}) => {
  const { t } = useTranslation();

  if (isSearching) {
    return (
      <div className="mt-6">
        <div className="text-2xl font-bold">
          {t('discover.search.searching')}
        </div>
        <div className="mt-3 grid grid-cols-1 gap-6 md:grid-cols-2">
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
        <div className="mt-3 grid grid-cols-1 gap-6 md:grid-cols-2">
          {results.map((bot) => (
            <CardBot
              key={bot.id}
              title={bot.title}
              description={bot.description}
              id={bot.id}
              sharedStatus={bot.sharedStatus}
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
