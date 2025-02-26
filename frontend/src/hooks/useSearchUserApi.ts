import {
  SearchUserGroupRequest,
  SearchUserGroupResponse,
  SearchUserRequest,
  SearchUserResponse,
} from '../@types/user';
import useHttp from './useHttp';

const useSearchUserApi = () => {
  const http = useHttp();

  return {
    searchUser: (prefix: string) => {
      const req: SearchUserRequest = {
        prefix,
      };
      return http.get<SearchUserResponse>(prefix ? ['user/search', req] : null);
    },
    searchUserGroup: (prefix: string) => {
      const req: SearchUserGroupRequest = {
        prefix,
      };
      return http.get<SearchUserGroupResponse>(
        prefix ? ['user/group/search', req] : null
      );
    },
  };
};

export default useSearchUserApi;
