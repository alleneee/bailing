import React, { useState, useEffect, useCallback } from 'react';
import { IconButton, CircularProgress } from '@mui/material';
import { Mic as MicIcon, Stop as StopIcon } from '@mui/icons-material';
import '../types';

interface VoiceControlProps {
  onResult: (text: string) => void;
  disabled?: boolean;
}

export const VoiceControl: React.FC<VoiceControlProps> = ({ onResult, disabled }) => {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'zh-CN';
        setRecognition(recognition);
      }
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognition) {
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const last = event.results.length - 1;
        const text = event.results[last][0].transcript;
        
        if (event.results[last].isFinal) {
          onResult(text);
          stopListening();
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('语音识别错误:', event.error);
        stopListening();
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      try {
        recognition.start();
        setIsListening(true);
      } catch (error) {
        console.error('启动语音识别失败:', error);
      }
    }
  }, [recognition, onResult]);

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  }, [recognition]);

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!recognition) {
    return (
      <IconButton color="primary" disabled>
        <MicIcon />
      </IconButton>
    );
  }

  return (
    <IconButton
      color="primary"
      onClick={toggleListening}
      disabled={disabled}
    >
      {isListening ? (
        <>
          <StopIcon />
          <CircularProgress
            size={24}
            sx={{
              position: 'absolute',
              color: 'primary.main',
            }}
          />
        </>
      ) : (
        <MicIcon />
      )}
    </IconButton>
  );
}; 