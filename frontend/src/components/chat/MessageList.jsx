import React, { useEffect, useRef } from 'react';
import Message from './Message';

/**
 * Scrollable message list.
 * Auto-scrolls to bottom on new messages.
 * Renders the loading placeholder while the AI is processing.
 */
const MessageList = React.memo(function MessageList({ messages, isLoading, onRegenerate, onCopy }) {
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="message-list" role="log" aria-live="polite" aria-label="Conversation">
            {(() => {
        let lastFile = null;
        return messages.map((msg, index) => {
          if (msg.uploadedFiles && msg.uploadedFiles.length > 0) {
            lastFile = msg.uploadedFiles[0];
          }
          return (
            <Message
              key={msg.id}
              message={{...msg, activeFile: lastFile}}
              onRegenerate={index === messages.length - 1 ? onRegenerate : null}
              onCopy={onCopy}
            />
          );
        });
      })()}

      {/* AI loading placeholder */}
      {isLoading && (
        <Message
          message={{
            id: '__loading__',
            role: 'assistant',
            content: '',
            isLoading: true,
            timestamp: null,
            uploadedFiles: [],
            analysis: null,
            error: null,
          }}
        />
      )}

      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
});

export default MessageList;

