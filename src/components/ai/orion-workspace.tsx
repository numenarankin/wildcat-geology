"use client";

import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import type { UIMessage } from "ai";
import { uuid } from "@/lib/utils";
import { OrionConversationList } from "@/components/ai/orion-conversation-list";
import { OrionChat } from "@/components/ai/orion-chat";
import {
  deleteConversation,
  saveMessages,
} from "@/lib/ai/conversation-actions";
import { NEW_CHAT_TITLE, type Conversation } from "@/lib/ai/conversations";

/**
 * A fresh, unsaved conversation. It only becomes a DB row once the user sends a
 * message (via `saveMessages`), so empty "New chat" entries never get persisted.
 */
function makeDraft(): Conversation {
  const now = Date.now();
  return {
    id: uuid(),
    title: NEW_CHAT_TITLE,
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

/** What a host page can drive from outside, e.g. the project toolbar's New Chat. */
export interface OrionWorkspaceHandle {
  newChat: () => void;
}

export function OrionWorkspace({
  initialConversations,
  firstName,
  folderId,
  projectName,
  ref,
}: {
  initialConversations: Conversation[];
  /** Signed-in user's first name, for the new-chat greeting (matches home). */
  firstName: string;
  /**
   * When set, this is the project-embedded Orion: chats are folder-scoped
   * (retrieval + prompt) and saved tagged to the folder so they surface in the
   * project's history. Omitted on the global /orion page.
   */
  folderId?: string;
  projectName?: string;
  ref?: React.Ref<OrionWorkspaceHandle>;
}) {
  const [conversations, setConversations] = useState(initialConversations);
  const [activeId, setActiveId] = useState<string | null>(null);
  // The pending debounced save, tagged with the thread it would write. Deleting
  // that thread has to cancel it, or the save lands after the delete and puts
  // the conversation straight back.
  const saveTimer = useRef<{
    id: string;
    timer: ReturnType<typeof setTimeout>;
  } | null>(null);
  // Open a fresh chat whenever the page mounts. Both a fresh login and any
  // in-app navigation TO this page remount the component, so each lands the user
  // on a new chat, with prior conversations tucked into the history card. A
  // dormant tab regaining focus does NOT remount (and nothing here watches tab
  // visibility), so switching back to it leaves the current chat exactly as it
  // was. The ref keeps this to a single seed under StrictMode double-invocation.
  const startedRef = useRef(false);
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    // Create the draft once in the effect body (not inside the setConversations
    // updater): React double-invokes updaters in dev/StrictMode, which would mint
    // two drafts and leave activeId pointing at the one NOT in the list — a blank
    // chat. Hoisting keeps the list entry and activeId referring to the same draft.
    const draft = makeDraft();
    setConversations((prev) => [draft, ...prev]);
    setActiveId(draft.id);
  }, []);

  const handleCreate = useCallback(() => {
    // Draft minted once outside the updater so StrictMode's double-invoke can't
    // desync the list entry from activeId (see the mount effect above).
    const draft = makeDraft();
    setConversations((prev) => {
      // Reuse an existing empty conversation instead of stacking blank drafts.
      const existingEmpty = prev.find((c) => c.messages.length === 0);
      if (existingEmpty) {
        setActiveId(existingEmpty.id);
        return prev;
      }
      setActiveId(draft.id);
      return [draft, ...prev];
    });
  }, []);

  // Same "New chat" the history panel offers, exposed so a host page's own
  // button (the project toolbar) opens a chat here rather than duplicating the
  // draft/reuse rules.
  useImperativeHandle(ref, () => ({ newChat: handleCreate }), [handleCreate]);

  const handleDelete = useCallback(
    (id: string) => {
      // Cancel a save still owed to this thread. It carries the messages that
      // were just deleted, and `saveMessages` upserts, so letting it fire would
      // recreate the row seconds after it went away.
      if (saveTimer.current?.id === id) {
        clearTimeout(saveTimer.current.timer);
        saveTimer.current = null;
      }

      const remaining = conversations.filter((c) => c.id !== id);

      if (activeId === id) {
        // Deleting the chat you are READING lands you on a new chat, not on the
        // next thread down. The panel is a history; opening some other
        // conversation the reader did not ask for reads as the delete having
        // gone somewhere at random, and it leaves them in a thread they may
        // have meant to keep closed. An existing empty draft is reused rather
        // than stacking blanks, matching "New chat".
        const draft = remaining.find((c) => c.messages.length === 0) ?? makeDraft();
        setConversations(
          remaining.includes(draft) ? remaining : [draft, ...remaining]
        );
        setActiveId(draft.id);
      } else {
        setConversations(remaining);
      }

      // No-op for drafts that were never persisted.
      deleteConversation(id).catch((error) =>
        console.error("Failed to delete conversation", error)
      );
    },
    [conversations, activeId]
  );

  const handleMessagesChange = useCallback(
    (messages: UIMessage[]) => {
      if (!activeId) return;
      const id = activeId;
      setConversations((prev) =>
        prev.map((c) =>
          c.id === id
            ? {
                ...c,
                messages,
                /*
                 * The panel's clock, live.
                 *
                 * `updatedAt` came from the server on page load and was never
                 * touched again, so a conversation being written in RIGHT NOW
                 * still showed its age at load — "15m" against a message
                 * stamped a minute ago. The row itself is correct; the copy in
                 * memory was frozen.
                 *
                 * Safe to stamp `now` here because this callback no longer
                 * fires for merely opening a chat (see the `dirty` gate in
                 * `orion-chat.tsx`) — it means the user actually said
                 * something, which is exactly what this column should track.
                 */
                updatedAt: Date.now(),
              }
            : c
        )
      );
      // Don't persist an empty conversation; only save once there's content.
      if (messages.length === 0) return;
      if (saveTimer.current) clearTimeout(saveTimer.current.timer);
      saveTimer.current = {
        id,
        timer: setTimeout(() => {
          saveTimer.current = null;
          // folderId tags the chat to the project (undefined on the global page).
          saveMessages(id, messages, folderId).catch((error) =>
            console.error("Failed to save messages", error)
          );
        }, 800),
      };
    },
    [activeId, folderId]
  );

  const active = conversations.find((c) => c.id === activeId) ?? null;

  return (
    // `relative` is the collapsed history strip's positioning context: folded,
    // the list floats in the chat's left gutter rather than taking width.
    <div className="relative flex min-h-0 flex-1 overflow-hidden bg-background">
      <OrionConversationList
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
      {/* The chat owns its own positioning context: its composer floats against
          this box, so the history panel beside it costs the conversation width
          and nothing else. */}
      <div className="relative flex min-w-0 flex-1">
        {active && (
          <OrionChat
            key={active.id}
            conversation={active}
            onMessagesChange={handleMessagesChange}
            firstName={firstName}
            folderId={folderId}
            projectName={projectName}
          />
        )}
      </div>
    </div>
  );
}
