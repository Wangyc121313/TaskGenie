/**
 * useVoiceInput
 *
 * Wraps @react-native-voice/voice to provide a simple recording toggle.
 *
 * Usage:
 *   const { listening, start, stop, error } = useVoiceInput({
 *     onResult: (text) => setPrompt(text),
 *     locale: 'zh-CN',          // optional, defaults to device locale
 *   });
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { PermissionsAndroid, Platform } from 'react-native';

// @react-native-voice/voice uses a default export
let Voice;
try {
  Voice = require('@react-native-voice/voice').default;
} catch (_) {
  Voice = null;
}

export const useVoiceInput = ({ onResult, locale } = {}) => {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState(null);
  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;

  useEffect(() => {
    if (!Voice) return;

    const onSpeechResults = (event) => {
      const text = event?.value?.[0];
      if (text) {
        onResultRef.current?.(text);
      }
      setListening(false);
    };

    const onSpeechError = (event) => {
      const msg = event?.error?.message || '语音识别出错';
      // error code 7 = "No match" (user stopped without speaking) — treat as silent cancel
      if (!msg.includes('7/')) {
        setError(msg);
      }
      setListening(false);
    };

    const onSpeechEnd = () => setListening(false);

    Voice.onSpeechResults = onSpeechResults;
    Voice.onSpeechError = onSpeechError;
    Voice.onSpeechEnd = onSpeechEnd;

    return () => {
      Voice.destroy().catch(() => {});
      Voice.onSpeechResults = null;
      Voice.onSpeechError = null;
      Voice.onSpeechEnd = null;
    };
  }, []);

  const requestPermission = useCallback(async () => {
    if (Platform.OS !== 'android') return true;
    const status = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      {
        title: '需要麦克风权限',
        message: 'TaskGenie 需要访问麦克风以进行语音输入',
        buttonPositive: '允许',
        buttonNegative: '拒绝',
      },
    );
    return status === PermissionsAndroid.RESULTS.GRANTED;
  }, []);

  const start = useCallback(async () => {
    if (!Voice) {
      setError('语音识别不可用');
      return;
    }
    setError(null);
    const granted = await requestPermission();
    if (!granted) {
      setError('麦克风权限被拒绝');
      return;
    }
    try {
      await Voice.start(locale || 'zh-CN');
      setListening(true);
    } catch (err) {
      setError(err.message || '无法启动语音识别');
    }
  }, [locale, requestPermission]);

  const stop = useCallback(async () => {
    if (!Voice) return;
    try {
      await Voice.stop();
    } catch (_) {
      // ignore
    }
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) {
      stop();
    } else {
      start();
    }
  }, [listening, start, stop]);

  return { listening, start, stop, toggle, error, available: !!Voice };
};
