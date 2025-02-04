import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Container,
  Stack,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { RootState } from '../store';
import { addMessage } from '../store/chatSlice';
import { Message } from './Message';
import { VoiceControl } from './VoiceControl';
import { useWebSocket } from '../hooks/useWebSocket';

export const Chat: React.FC = () => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dispatch = useDispatch();
  const { messages, isConnected } = useSelector((state: RootState) => state.chat);
  const { sendMessage } = useWebSocket();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      const message = {
        role: 'user' as const,
        content: input.trim()
      };
      dispatch(addMessage(message));
      sendMessage(message);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceResult = (text: string) => {
    if (text.trim()) {
      const message = {
        role: 'user' as const,
        content: text.trim()
      };
      dispatch(addMessage(message));
      sendMessage(message);
    }
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', py: 2 }}>
      <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          <Stack spacing={2}>
            {messages.map((msg, index) => (
              <Message key={index} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </Stack>
        </Box>
        
        <Box sx={{ p: 2, backgroundColor: 'background.default' }}>
          {!isConnected && (
            <Typography color="error" variant="caption" display="block" gutterBottom>
              未连接到服务器
            </Typography>
          )}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息..."
              variant="outlined"
              size="small"
            />
            <IconButton
              color="primary"
              onClick={handleSend}
              disabled={!input.trim() || !isConnected}
            >
              <SendIcon />
            </IconButton>
            <VoiceControl
              onResult={handleVoiceResult}
              disabled={!isConnected}
            />
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}; 