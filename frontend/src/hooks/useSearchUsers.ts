import { useEffect, useMemo } from 'react';
import useUserApi from './useUserApi';
import { SearchedUser } from '../@types/user';

const useSearchUsers = (prefix: string) => {
  const { searchUsers, searchUserGroups } = useUserApi();

  const {
    data: users,
    isLoading: isLoadingUsers,
    isValidating,
  } = searchUsers(prefix === '' ? undefined : prefix);
  const { data: userGroups, isLoading: isLoadingUserGroups } = searchUserGroups(
    prefix === '' ? undefined : prefix
  );

  useEffect(() => {
    console.log(isValidating, isLoadingUsers);
  }, [isValidating, isLoadingUsers]);

  const searchedUsers = useMemo<SearchedUser[]>(() => {
    const users_: SearchedUser[] =
      users?.map((user) => ({
        type: 'user',
        ...user,
      })) ?? [];

    const userGroups_: SearchedUser[] =
      userGroups?.map((group) => ({
        type: 'group',
        ...group,
      })) ?? [];

    return users_
      .concat(userGroups_)
      .sort((a, b) => (a.name >= b.name ? 1 : -1));
  }, [users, userGroups]);

  const isLoading = useMemo(() => {
    return isLoadingUsers || isLoadingUserGroups;
  }, [isLoadingUsers, isLoadingUserGroups]);

  return {
    searchedUsers,
    isLoading,
  };
};

export default useSearchUsers;
