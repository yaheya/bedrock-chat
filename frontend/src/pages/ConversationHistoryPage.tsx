import React, { useCallback, useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PiCheck, PiPencilLine, PiPlus, PiTrash, PiX } from 'react-icons/pi';
import { useNavigate } from 'react-router-dom';
import useConversation from '../hooks/useConversation';
import { ConversationMeta } from '../@types/conversation';
import ButtonIcon from '../components/ButtonIcon';
import useChat from '../hooks/useChat';
import DialogConfirmDeleteChat from '../components/DialogConfirmDeleteChat';
import Button from '../components/Button';
import ListPageLayout from '../layouts/ListPageLayout';

const ConversationHistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isOpenDeleteDialog, setIsOpenDeleteDialog] = useState(false);
  const [targetConversation, setTargetConversation] =
    useState<ConversationMeta>();
  const [editingConversationId, setEditingConversationId] = useState<
    string | null
  >(null);
  const [tempTitle, setTempTitle] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const { setConversationId, newChat } = useChat();
  const {
    conversations,
    deleteConversation,
    updateTitle,
    isLoadingConversations,
  } = useConversation();

  const onClickNewChat = useCallback(() => {
    newChat();
    navigate('/');
  }, [newChat, navigate]);

  const onClickDelete = useCallback(
    (e: React.MouseEvent, conversation: ConversationMeta) => {
      e.stopPropagation();
      setIsOpenDeleteDialog(true);
      setTargetConversation(conversation);
    },
    []
  );

  const onClickEdit = useCallback(
    (e: React.MouseEvent, conversation: ConversationMeta) => {
      e.stopPropagation();
      setEditingConversationId(conversation.id);
      setTempTitle(conversation.title);
    },
    []
  );

  const onDeleteConversation = useCallback(() => {
    if (targetConversation) {
      setIsOpenDeleteDialog(false);

      // Deletion process including optimistic update is handled in useConversation
      deleteConversation(targetConversation.id).catch(() => {
        setIsOpenDeleteDialog(true);
      });
    }
  }, [deleteConversation, targetConversation]);

  const onUpdateTitle = useCallback(
    (conversationId: string, title: string) => {
      // Exit edit mode
      setEditingConversationId(null);

      // Update process including optimistic update is handled in useConversation
      updateTitle(conversationId, title);
    },
    [updateTitle]
  );

  const onClickConversation = useCallback(
    (conversationId: string) => {
      if (editingConversationId !== conversationId) {
        setConversationId(conversationId);
        navigate(`/${conversationId}`);
      }
    },
    [navigate, setConversationId, editingConversationId]
  );

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  useLayoutEffect(() => {
    if (editingConversationId && inputRef.current) {
      inputRef.current.focus();
    }
  }, [editingConversationId]);

  useLayoutEffect(() => {
    if (editingConversationId && inputRef.current) {
      const listener = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          onUpdateTitle(editingConversationId, tempTitle);
        } else if (e.key === 'Escape') {
          setEditingConversationId(null);
        }
      };

      const currentRef = inputRef.current;

      currentRef.addEventListener('keydown', listener);
      return () => {
        currentRef.removeEventListener('keydown', listener);
      };
    }
  }, [editingConversationId, tempTitle, onUpdateTitle]);

  return (
    <>
      <DialogConfirmDeleteChat
        isOpen={isOpenDeleteDialog}
        target={targetConversation}
        onDelete={onDeleteConversation}
        onClose={() => {
          setIsOpenDeleteDialog(false);
        }}
      />

      <ListPageLayout
        pageTitle={t('conversationHistory.pageTitle')}
        pageTitleActions={
          <Button
            className="text-sm"
            outlined
            icon={<PiPlus />}
            onClick={onClickNewChat}>
            {t('button.newChat')}
          </Button>
        }
        isLoading={isLoadingConversations}
        isEmpty={conversations?.length === 0}
        emptyMessage={t('conversationHistory.label.noConversations')}>
        {conversations?.map((conversation) => (
          <div
            key={conversation.id}
            className="group flex cursor-pointer items-center justify-between border-b border-gray p-2 hover:bg-light-gray"
            onClick={() => onClickConversation(conversation.id)}>
            <div className="flex flex-col">
              {editingConversationId === conversation.id ? (
                <div
                  className="flex items-center"
                  onClick={(e) => e.stopPropagation()}>
                  <input
                    ref={inputRef}
                    type="text"
                    className="w-64 bg-transparent text-base"
                    value={tempTitle}
                    onChange={(e) => setTempTitle(e.target.value)}
                  />
                  <ButtonIcon
                    className="text-base"
                    onClick={() => onUpdateTitle(conversation.id, tempTitle)}
                    disabled={
                      !tempTitle.trim() ||
                      tempTitle.trim() === conversation.title
                    }>
                    <PiCheck />
                  </ButtonIcon>
                  <ButtonIcon
                    className="text-base"
                    onClick={() => setEditingConversationId(null)}>
                    <PiX />
                  </ButtonIcon>
                </div>
              ) : (
                <div className="flex items-center">
                  <div className="text-base font-medium">
                    {conversation.title}
                  </div>
                  <ButtonIcon
                    className="-my-2 mr-6 opacity-0 group-hover:opacity-100"
                    onClick={(e) => onClickEdit(e, conversation)}>
                    <PiPencilLine />
                  </ButtonIcon>
                </div>
              )}
              <div className="text-xs text-gray">
                {formatDate(conversation.createTime)}
              </div>
            </div>
            {editingConversationId !== conversation.id && (
              <div className="flex items-center opacity-0 group-hover:opacity-100">
                <ButtonIcon onClick={(e) => onClickDelete(e, conversation)}>
                  <PiTrash />
                </ButtonIcon>
              </div>
            )}
          </div>
        ))}
      </ListPageLayout>
    </>
  );
};

export default ConversationHistoryPage;
