import { useCallback, useState } from 'react';
import { Alert } from 'react-native';

import { API_URL } from '../context/TaskContext';


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
      const response = await fetch(`${API_URL}/ai/agent/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
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
      const response = await fetch(`${API_URL}/ai/agent/runs/${jobId}/confirm`, {
        method: 'POST',
      });
      const data = await response.json();
      if (!response.ok) {
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
