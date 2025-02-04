import React, { useEffect, useState } from 'react';
import { Paper, Typography, Box, IconButton } from '@mui/material';
import { VolumeUp, VolumeOff } from '@mui/icons-material';

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
  };
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  const speak = async () => {
    if (!isUser && message.content) {
      try {
        // 停止当前正在播放的音频
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
        }

        // 创建新的音频实例
        const response = await fetch('http://localhost:8000/tts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text: message.content }),
        });

        if (!response.ok) {
          throw new Error('TTS请求失败');
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const newAudio = new Audio(audioUrl);
        
        newAudio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };

        setAudio(newAudio);
        setIsPlaying(true);
        await newAudio.play();
      } catch (error) {
        console.error('语音播放错误:', error);
        setIsPlaying(false);
      }
    }
  };

  const stopSpeak = () => {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      setIsPlaying(false);
    }
  };

  // 当消息是助手的回复时，自动播放
  useEffect(() => {
    if (!isUser && message.content) {
      speak();
    }
  }, [message.content, isUser]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (audio) {
        audio.pause();
        setIsPlaying(false);
      }
    };
  }, [audio]);

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          maxWidth: '70%',
          backgroundColor: isUser ? 'primary.light' : 'background.paper',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          position: 'relative',
        }}
      >
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
          {message.content}
        </Typography>
        {!isUser && (
          <IconButton
            size="small"
            onClick={isPlaying ? stopSpeak : speak}
            sx={{
              position: 'absolute',
              right: 8,
              bottom: 8,
            }}
          >
            {isPlaying ? <VolumeOff fontSize="small" /> : <VolumeUp fontSize="small" />}
          </IconButton>
        )}
      </Paper>
    </Box>
  );
}; 