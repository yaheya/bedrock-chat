import React, { useEffect, useRef, useState } from 'react';
import Button from './Button';
import { PiList, PiSignOut, PiTranslate, PiTrash } from 'react-icons/pi';
import { useTranslation } from 'react-i18next';
import { BaseProps } from '../@types/common';
import { twMerge } from 'tailwind-merge';
import useLoginUser from '../hooks/useLoginUser';

type Props = BaseProps & {
  onSignOut: () => void;
  onSelectLanguage: () => void;
  onClearConversations: () => void;
};

// 認証時に表示するメニューコンポーネント
const MenuSettings: React.FC<Props> = (props) => {
  const { t } = useTranslation();
  const { userGroups, userName } = useLoginUser();

  const [isOpen, setIsOpen] = useState(false);

  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // メニューの外側をクリックした際のハンドリング
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleClickOutside = (event: any) => {
      // メニューボタンとメニュー以外をクリックしていたらメニューを閉じる
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target) &&
        !buttonRef.current?.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };
    // イベントリスナーを設定
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      // 後処理でイベントリスナーを削除
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuRef]);

  return (
    <>
      <Button
        ref={buttonRef}
        className={twMerge('relative bg-aws-squid-ink', props.className)}
        text
        icon={<PiList />}
        onClick={() => {
          setIsOpen(!isOpen);
        }}>
        {t('button.menu')}
      </Button>

      {isOpen && (
        <div
          ref={menuRef}
          className="absolute bottom-10 left-2 w-60 rounded border border-aws-font-color-white bg-aws-sea-blue text-aws-font-color-white">
          <div className="flex flex-col gap-1 border-b p-2">
            <div className="font-bold">{userName}</div>
            <div className="">
              <div className="italic">{t('app.userGroups')}</div>
              <ul className="list-disc pl-5">
                {userGroups.map((group) => (
                  <li key={group}>{group}</li>
                ))}
              </ul>
            </div>
          </div>

          <div
            className="flex w-full cursor-pointer items-center p-2 hover:bg-aws-sea-blue-hover"
            onClick={() => {
              setIsOpen(false);
              props.onSelectLanguage();
            }}>
            <PiTranslate className="mr-2" />
            {t('button.language')}
          </div>
          <div
            className="flex w-full cursor-pointer items-center p-2 hover:bg-aws-sea-blue-hover"
            onClick={() => {
              setIsOpen(false);
              props.onClearConversations();
            }}>
            <PiTrash className="mr-2" />
            {t('button.clearConversation')}
          </div>
          <div
            className="flex w-full cursor-pointer items-center border-t p-2 hover:bg-aws-sea-blue-hover"
            onClick={props.onSignOut}>
            <PiSignOut className="mr-2" />
            {t('button.signOut')}
          </div>
        </div>
      )}
    </>
  );
};

export default MenuSettings;
