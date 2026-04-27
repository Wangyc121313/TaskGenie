import { useCallback, useState } from 'react';
import { Alert } from 'react-native';

import { apiFetch } from '../utils/api';


export const useAgentAssistant = ({ onTasksChanged } = {}) => {
  const [currentRun, setCurrentRun] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCompletedSideEffects = useCallback(async response => {
    const createdTasks = response?.artifacts?.created_tasks || [];
    if (createdTasks.length && onTasksChanged) {
      await onTasksChanged();
    }
  }, [onTasksChanged]);

  const runAgent = useCallback(async payload => {
    setLoading(true);
    try {
      const { ok, data } = await apiFetch('/ai/agent/run', {
        method: 'POST',
        body: payload,
      });
      if (!ok) {
        Alert.alert('Agent Error', data.detail || data.error || 'Failed to run agent.');
        return null;
      }

      setCurrentRun(data);
      await handleCompletedSideEffects(data);
      return data;
    } catch (error) {
      console.error(error);
      Alert.alert('Agent Error', 'Failed to run agent.');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleCompletedSideEffects]);

  const confirmRun = useCallback(async jobId => {
    setLoading(true);
    try {
      const { ok, data } = await apiFetch(`/ai/agent/runs/${jobId}/confirm`, {
        method: 'POST',
      });
      if (!ok) {
        Alert.alert('Agent Error', data.detail || data.error || 'Failed to confirm agent run.');
        return null;
      }

      setCurrentRun(data);
      await handleCompletedSideEffects(data);
      return data;
    } catch (error) {
      console.error(error);
      Alert.alert('Agent Error', 'Failed to confirm agent run.');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleCompletedSideEffects]);

  return {
    currentRun,
    loading,
    runAgent,
    confirmRun,
    clearRun: () => setCurrentRun(null),
  };
};
