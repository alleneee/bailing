import React, { useState, useEffect } from 'react';
import { Avatar, Box, IconButton, Typography } from '@mui/material';
import { VolumeOff, VolumeUp } from '@mui/icons-material';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatProps {
  messages: Message[];
}

const Chat: React.FC<ChatProps> = ({ messages }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  const speak = async (text: string) => {
    try {
      if (isPlaying && audio) {
        audio.pause();
        setIsPlaying(false);
        return;
      }

      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const error = await response.json();
        console.error('TTS错误:', error);
        return;
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audio) {
        audio.src = audioUrl;
      } else {
        const newAudio = new Audio(audioUrl);
        setAudio(newAudio);
        newAudio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };
        newAudio.onerror = (e) => {
          console.error('音频播放错误:', e);
          setIsPlaying(false);
        };
        newAudio.play();
      }
      setIsPlaying(true);
    } catch (error) {
      console.error('TTS处理错误:', error);
      setIsPlaying(false);
    }
  };

  return (
    <Box>
      {messages.map((message, index) => (
        <Box key={index} sx={{ display: 'flex', mb: 2, alignItems: 'flex-start' }}>
          <Avatar sx={{ mr: 2, bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main' }}>
            {message.role === 'user' ? 'U' : 'A'}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body1">{message.content}</Typography>
          </Box>
          {message.role === 'assistant' && (
            <IconButton 
              onClick={() => speak(message.content)}
              sx={{ ml: 1 }}
            >
              {isPlaying ? <VolumeOff /> : <VolumeUp />}
            </IconButton>
          )}
        </Box>
      ))}
    </Box>
  );
};

export default Chat; 