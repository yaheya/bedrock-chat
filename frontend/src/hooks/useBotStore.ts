import useBotApi from './useBotApi';
import useBotStoreApi from './useBotStoreApi';

const useBotStore = () => {
  const { getPickupBots, getPopularBots } = useBotStoreApi();
  const { getPinnedBots } = useBotApi();

  const { data: pickupBots, isLoading: isLoadingPickupBots } = getPickupBots();
  const { data: popularBots, isLoading: isLoadingPopularBots } =
    getPopularBots();
  const { data: pinnedBots, isLoading: isLoadingPinnedBots } = getPinnedBots();

  return {
    pinnedBots: pinnedBots ?? [],
    isLoadingPinnedBots,
    popularBots: popularBots ?? [],
    isLoadingPopularBots,
    pickupBots: pickupBots ?? [],
    isLoadingPickupBots,
  };
};

export default useBotStore;
