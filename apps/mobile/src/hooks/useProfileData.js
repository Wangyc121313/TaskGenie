import { useCallback, useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { apiFetch } from '../utils/api';


const DEFAULT_PREFERENCES = {
  display_name: '',
  work_start_time: '09:00',
  work_end_time: '18:00',
  planning_style: 'balanced',
  priority_preference: 'balanced',
  peak_focus_period: 'morning',
  max_daily_focus_hours: 6,
  preferred_task_duration_hours: 2,
  break_interval_minutes: 90,
  avoid_time_ranges: [],
};


export const useProfileData = () => {
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const [preferencesResult, memoriesResult] = await Promise.all([
        apiFetch('/profile/preferences'),
        apiFetch('/profile/memories'),
      ]);

      if (preferencesResult.ok) {
        setPreferences(preferencesResult.data);
      }
      if (memoriesResult.ok) {
        setMemories(memoriesResult.data);
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Profile Error', 'Failed to load profile data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const updatePreferences = useCallback(async payload => {
    try {
      const { ok, data } = await apiFetch('/profile/preferences', {
        method: 'PUT',
        body: payload,
      });
      if (!ok) {
        Alert.alert('Profile Error', data.detail || 'Failed to update preferences.');
        return null;
      }
      setPreferences(data);
      return data;
    } catch (error) {
      console.error(error);
      Alert.alert('Profile Error', 'Failed to update preferences.');
      return null;
    }
  }, []);

  const createMemory = useCallback(async payload => {
    try {
      const { ok, data } = await apiFetch('/profile/memories', {
        method: 'POST',
        body: payload,
      });
      if (!ok) {
        Alert.alert('Profile Error', data.detail || 'Failed to create memory.');
        return null;
      }
      setMemories(prevState => [data, ...prevState]);
      return data;
    } catch (error) {
      console.error(error);
      Alert.alert('Profile Error', 'Failed to create memory.');
      return null;
    }
  }, []);

  const updateMemory = useCallback(async (memoryId, payload) => {
    try {
      const { ok, data } = await apiFetch(`/profile/memories/${memoryId}`, {
        method: 'PUT',
        body: payload,
      });
      if (!ok) {
        Alert.alert('Profile Error', data.detail || 'Failed to update memory.');
        return null;
      }
      setMemories(prevState =>
        prevState.map(memory => (memory.id === memoryId ? data : memory)),
      );
      return data;
    } catch (error) {
      console.error(error);
      Alert.alert('Profile Error', 'Failed to update memory.');
      return null;
    }
  }, []);

  const deleteMemory = useCallback(async memoryId => {
    try {
      const { ok, data } = await apiFetch(`/profile/memories/${memoryId}`, {
        method: 'DELETE',
      });
      if (!ok) {
        Alert.alert('Profile Error', data.detail || 'Failed to delete memory.');
        return false;
      }
      setMemories(prevState => prevState.filter(memory => memory.id !== memoryId));
      return true;
    } catch (error) {
      console.error(error);
      Alert.alert('Profile Error', 'Failed to delete memory.');
      return false;
    }
  }, []);

  return {
    preferences,
    memories,
    loading,
    updatePreferences,
    createMemory,
    updateMemory,
    deleteMemory,
    refreshProfile: fetchProfile,
  };
};
