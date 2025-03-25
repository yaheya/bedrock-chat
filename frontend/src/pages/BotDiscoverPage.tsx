import React, { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  PiBinoculars,
  PiCertificate,
  PiMagnifyingGlass,
  PiRanking,
  PiX,
} from 'react-icons/pi';
import InputText from '../components/InputText';
import useBotStore from '../hooks/useBotStore';
import { twMerge } from 'tailwind-merge';
import useBot from '../hooks/useBot';
import useBotSearch from '../hooks/useBotSearch';
import BotSearchResults, {
  CardBot,
  SkeletonBot,
} from '../components/BotSearchResults';
import { isPinnedBot } from '../utils/BotUtils';

const BotDiscoverPage: React.FC = () => {
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState('');

  const {
    pickupBots,
    isLoadingPickupBots,
    popularBots,
    isLoadingPopularBots,
    pinnedBots,
    toggleBotStarred,
  } = useBotStore();
  const { mutateStarredBots } = useBot();
  const {
    displayQuery, // Query used for displaying search results
    searchResults,
    isSearching,
    hasSearched,
    handleSearch,
    clearSearch,
    updateSearchResultStarredStatus,
  } = useBotSearch();

  const handleToggleStar = useCallback(
    (botId: string, starred: boolean) => {
      // Optimistic update for search results
      if (hasSearched) {
        updateSearchResultStarredStatus(botId, starred);
      }

      // Optimistic update for regular bot lists and API call
      toggleBotStarred(botId, starred)
        .catch((error) => {
          console.error('Failed to update star status:', error);
          // Revert search results on error
          if (hasSearched) {
            updateSearchResultStarredStatus(botId, !starred);
          }
        })
        .finally(() => {
          // Refresh starred bots list
          mutateStarredBots();
        });
    },
    [
      mutateStarredBots,
      toggleBotStarred,
      hasSearched,
      updateSearchResultStarredStatus,
    ]
  );

  const handleInputChange = useCallback(
    (value: string) => {
      setInputValue(value);
      handleSearch(value); // Trigger search on input change for real-time search
    },
    [handleSearch]
  );

  const handleClearSearch = useCallback(() => {
    setInputValue('');
    clearSearch();
  }, [clearSearch]);

  // Show regular content when not searching
  const showRegularContent = useMemo(() => !hasSearched, [hasSearched]);

  return (
    <>
      <div className="mb-32 flex h-full justify-center">
        <div className="flex w-full max-w-screen-xl flex-col gap-3 px-4 pt-8 lg:w-4/5">
          <div className="flex justify-center text-4xl font-bold">
            {t('discover.pageTitle').toUpperCase()}
          </div>

          <div className=" flex w-full flex-col items-center justify-center text-dark-gray">
            <div>{t('discover.description')}</div>
          </div>

          <div className="relative mt-6">
            <InputText
              icon={<PiMagnifyingGlass />}
              placeholder={t('discover.search.placeholder')}
              value={inputValue}
              onChange={handleInputChange}
            />
            {inputValue && (
              <button
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray hover:text-dark-gray"
                onClick={handleClearSearch}>
                <PiX size={20} />
              </button>
            )}
          </div>

          {/* Search Results */}
          <BotSearchResults
            results={searchResults}
            isSearching={isSearching}
            hasSearched={hasSearched}
            searchQuery={displayQuery}
            onToggleStar={handleToggleStar}
            onBackToHome={handleClearSearch}
          />

          {showRegularContent && (
            <>
              <div
                className={twMerge(
                  pinnedBots.length === 0 ? 'invisible h-0 scale-y-0' : 'mt-6',
                  'transition-all duration-300'
                )}>
                <div className="flex items-center text-2xl font-bold">
                  <PiCertificate className="mr-2" />
                  {t('discover.essential.label')}
                </div>
                <div className="mt-1 text-sm text-gray">
                  {t('discover.essential.description')}
                </div>

                <div className="mt-3 grid grid-cols-2 gap-6">
                  {pinnedBots.map((bot) => (
                    <CardBot
                      key={bot.id}
                      title={bot.title}
                      description={bot.description}
                      id={bot.id}
                      isStarred={bot.isStarred}
                      isPinned={isPinnedBot(bot.sharedScope)}
                      onToggleStar={handleToggleStar}
                    />
                  ))}
                </div>
              </div>

              <div className="mt-6">
                <div className="flex items-center text-2xl font-bold">
                  <PiRanking className="mr-2" />
                  {t('discover.trending.label')}
                </div>
                <div className="mt-1 text-sm text-gray">
                  {t('discover.trending.description')}
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
                          isPinned={isPinnedBot(bot.sharedScope)}
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
                  {t('discover.discover.label')}
                </div>
                <div className="mt-1 text-sm text-gray">
                  {t('discover.discover.description')}
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
                      isPinned={isPinnedBot(bot.sharedScope)}
                      onToggleStar={handleToggleStar}
                    />
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default BotDiscoverPage;
