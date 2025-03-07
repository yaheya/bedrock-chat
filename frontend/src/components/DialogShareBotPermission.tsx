import React, { useMemo, useState } from 'react';
import { BaseProps } from '../@types/common';
import Button from './Button';
import { useTranslation } from 'react-i18next';
import InputText from './InputText';
import { User, UserGroup } from '../@types/user';
import { PiMagnifyingGlass, PiUser, PiUsers } from 'react-icons/pi';
import Progress from './Progress';
import useUser from '../hooks/useUser';
import { produce } from 'immer';
import { twMerge } from 'tailwind-merge';
import useSearchUsers from '../hooks/useSearchUsers';
import Skeleton from './Skeleton';

type NewSharedItemProps = {
  label: string;
  onClickRemove: () => void;
};

const NewSharedItem: React.FC<NewSharedItemProps> = (props) => {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between">
      <div className="text-base font-bold">{props.label}</div>

      <Button outlined onClick={props.onClickRemove}>
        {t('bot.shareDialog.button.cancelAddition')}
      </Button>
    </div>
  );
};

type SharedItemProps = {
  label: string;
  removed?: boolean;
  onClickRemove: () => void;
};

const SharedItem: React.FC<SharedItemProps> = (props) => {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between">
      <div
        className={twMerge(
          'text-base',
          props.removed && 'font-bold line-through'
        )}>
        {props.label}
      </div>

      <Button outlined onClick={props.onClickRemove}>
        {props.removed
          ? t('bot.shareDialog.button.cancelRemoval')
          : t('bot.shareDialog.button.removeAccess')}
      </Button>
    </div>
  );
};

type SharedUserItemProps = {
  id: string;
  removed?: boolean;
  onClickRemove: () => void;
};

const SharedUserItem: React.FC<SharedUserItemProps> = (props) => {
  const { user, isLoading } = useUser(props.id);
  return (
    <>
      {isLoading ? (
        <Skeleton className="h-8 w-full" />
      ) : (
        <SharedItem {...props} label={user ? user.name : ''} />
      )}
    </>
  );
};

type Props = BaseProps & {
  allowedUserIds: string[];
  allowedGroupIds: string[];
  searchUsersPrefix: string;
  onChangeSearchUsersPrefix: (searchUserPrefix: string) => void;
  onUpdateAllowedUserAndGroup: (
    allowedUserIds: string[],
    allowedGroupIds: string[]
  ) => void;
  onCancel: () => void;
};

const DialogShareBotPermission: React.FC<Props> = (props) => {
  const { t } = useTranslation();

  const [addTargetGroups, setAddTargetGroups] = useState<UserGroup[]>([]);
  const [addTargetUsers, setAddTargetUsers] = useState<User[]>([]);
  const [removeTargetIds, setRemoveTargetIds] = useState<string[]>([]);

  const { searchedUsers, isLoading: isSearching } = useSearchUsers(
    props.searchUsersPrefix
  );

  const displaySearchedUsers = useMemo(() => {
    // exclude added items
    return searchedUsers.filter((user) => {
      if (user.type === 'user') {
        return !addTargetUsers.find((target) => target.id === user.id);
      } else {
        return !addTargetGroups.find((target) => target.name === user.name);
      }
    });
  }, [addTargetGroups, addTargetUsers, searchedUsers]);

  return (
    <div>
      <InputText
        value={props.searchUsersPrefix}
        placeholder={t('bot.shareDialog.label.search')}
        icon={<PiMagnifyingGlass />}
        onChange={(s) => {
          props.onChangeSearchUsersPrefix(s);
        }}
      />

      {props.searchUsersPrefix && (
        <div className="relative mt-0.5 flex max-h-[30vh] w-full flex-col gap-1 overflow-y-auto rounded border">
          {displaySearchedUsers.map((user, idx) => (
            <div
              key={idx}
              className="flex cursor-pointer items-center gap-2 rounded p-2 hover:bg-light-gray"
              onClick={() => {
                if (user.type === 'user') {
                  setAddTargetUsers((prev) => {
                    return produce(prev, (draft) => {
                      draft.push(user);
                    });
                  });
                } else {
                  setAddTargetGroups((prev) => {
                    return produce(prev, (draft) => {
                      draft.push(user);
                    });
                  });
                }
              }}>
              <div className="rounded-full border p-0.5">
                {user.type === 'user' ? (
                  <PiUser className="text-base" />
                ) : (
                  <PiUsers className="text-base" />
                )}
              </div>
              <div>{user.name}</div>
            </div>
          ))}
          {isSearching && (
            <div className="sticky bottom-0">
              <Progress thin />
            </div>
          )}
        </div>
      )}

      <div className="mt-2 flex max-h-[30vh] flex-col gap-1 overflow-y-auto">
        <div className="mt-3 font-bold text-gray">
          {t('bot.shareDialog.label.group')}
        </div>
        <div className="flex flex-col gap-3">
          {addTargetGroups.map((group) => (
            <NewSharedItem
              key={group.name}
              label={group.name}
              onClickRemove={() => {
                setAddTargetGroups((prev) => {
                  const foundIndex = prev.findIndex(
                    (v) => v.name === group.name
                  );
                  if (foundIndex > -1) {
                    return produce(prev, (draft) => {
                      draft.splice(foundIndex, 1);
                    });
                  }
                  return prev;
                });
              }}
            />
          ))}
          {props.allowedGroupIds.map((group, idx) => (
            <SharedItem
              key={idx}
              label={group}
              removed={removeTargetIds.includes(group)}
              onClickRemove={() => {
                setRemoveTargetIds((prev) => {
                  const foundIndex = prev.findIndex((v) => v === group);
                  return produce(prev, (draft) => {
                    if (foundIndex > -1) {
                      draft.splice(foundIndex, 1);
                    } else {
                      draft.push(group);
                    }
                  });
                });
              }}
            />
          ))}
        </div>
        <div className="mt-3 font-bold text-gray">
          {t('bot.shareDialog.label.user')}
        </div>
        <div className="flex flex-col gap-3">
          {addTargetUsers.map((user) => (
            <NewSharedItem
              key={user.id}
              label={user.name}
              onClickRemove={() => {
                setAddTargetUsers((prev) => {
                  const foundIndex = prev.findIndex((v) => v.id === user.id);
                  if (foundIndex > -1) {
                    return produce(prev, (draft) => {
                      draft.splice(foundIndex, 1);
                    });
                  }
                  return prev;
                });
              }}
            />
          ))}
          {props.allowedUserIds.map((user, idx) => (
            <SharedUserItem
              key={idx}
              id={user}
              removed={removeTargetIds.includes(user)}
              onClickRemove={() => {
                setRemoveTargetIds((prev) => {
                  const foundIndex = prev.findIndex((v) => v === user);
                  return produce(prev, (draft) => {
                    if (foundIndex > -1) {
                      draft.splice(foundIndex, 1);
                    } else {
                      draft.push(user);
                    }
                  });
                });
              }}
            />
          ))}
        </div>
      </div>

      <div className="my-3 border-t" />
      <div className="flex justify-end gap-2">
        <Button outlined onClick={props.onCancel}>
          {t('button.cancel')}
        </Button>

        <Button
          onClick={() => {
            const allowedUserIds_ = addTargetUsers
              .map((user) => user.id)
              .concat(props.allowedUserIds)
              .filter((userId) => !removeTargetIds.includes(userId));
            const allowedGroupIds_ = addTargetGroups
              .map((group) => group.name)
              .concat(props.allowedGroupIds)
              .filter((groupId) => !removeTargetIds.includes(groupId));

            props.onUpdateAllowedUserAndGroup(
              allowedUserIds_,
              allowedGroupIds_
            );
          }}
          className="p-2">
          {t('button.done')}
        </Button>
      </div>
    </div>
  );
};

export default DialogShareBotPermission;
