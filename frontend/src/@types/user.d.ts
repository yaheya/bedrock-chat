export type User = {
  id: string;
  name: string;
  email: string;
};
export type UserGroup = {
  name: string;
  description: string;
};

export type SearchUserRequest = {
  prefix: string;
};
export type SearchUserResponse = User[];

export type SearchUserGroupRequest = {
  prefix: string;
};
export type SearchUserGroupResponse = UseGroup[];
