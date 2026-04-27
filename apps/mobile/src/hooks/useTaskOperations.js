import { useCallback, useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { apiFetch } from '../utils/api';


export const useTaskOperations = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [imagePlanningLoading, setImagePlanningLoading] = useState(false);
  const [aiJobId, setAiJobId] = useState(null);

  const fetchTasks = useCallback(async () => {
    try {
      const { ok, data } = await apiFetch('/tasks');
      if (ok) {
        setTasks(data);
      }
    } catch (error) {
      Alert.alert('错误', '加载任务失败。');
      console.error(error);
    }
  }, []);

  const createTask = async (taskData, options = {}) => {
    const { refresh = true, showAlert = false } = options;
    try {
      const { ok, data } = await apiFetch('/tasks', {
        method: 'POST',
        body: taskData,
      });

      if (!ok) {
        Alert.alert('错误', data.detail || '创建任务失败，请检查输入并重试');
        return false;
      }

      if (refresh) {
        await fetchTasks();
      }
      if (showAlert) {
        Alert.alert('成功', '任务已创建。');
      }
      return true;
    } catch (error) {
      Alert.alert('错误', '无法连接服务器，请确认 API 已启动。');
      console.error(error);
      return false;
    }
  };

  const createTasksFromCandidates = async (taskCandidates, contextTitle = '') => {
    let successCount = 0;
    for (const candidate of taskCandidates) {
      const normalizedName = contextTitle
        ? `${contextTitle}: ${candidate.name}`
        : candidate.name;

      const created = await createTask(
        {
          name: normalizedName,
          description: candidate.source_snippet
            ? `${candidate.description}\n\nSource: ${candidate.source_snippet}`
            : candidate.description,
          priority: candidate.priority,
          due_date: candidate.due_date || null,
          estimated_hours: candidate.estimated_hours || null,
        },
        { refresh: false },
      );
      if (created) {
        successCount += 1;
      }
    }

    await fetchTasks();
    return successCount;
  };

  const updateTask = async (taskId, updateData) => {
    try {
      const payload = Object.prototype.hasOwnProperty.call(updateData, 'completed')
        ? { completed: updateData.completed }
        : updateData;

      const { ok } = await apiFetch(`/tasks/${taskId}`, {
        method: 'PUT',
        body: payload,
      });

      if (!ok) {
        Alert.alert('错误', '更新任务失败，请重试。');
        return false;
      }

      await fetchTasks();
      return true;
    } catch (error) {
      Alert.alert('错误', '无法连接服务器，请确认 API 已启动。');
      console.error(error);
      return false;
    }
  };

  const toggleTaskCompletion = async (taskId, currentCompleted) => {
    try {
      const { ok } = await apiFetch(`/tasks/${taskId}`, {
        method: 'PUT',
        body: { completed: !currentCompleted },
      });

      if (!ok) {
        return false;
      }

      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === taskId
            ? {
                ...task,
                completed: !currentCompleted,
              }
            : task,
        ),
      );

      await fetchTasks();
      return true;
    } catch (error) {
      Alert.alert('错误', '无法连接服务器，请确认 API 已启动。');
      console.error(error);
      await fetchTasks();
      return false;
    }
  };

  const deleteTask = async taskId => {
    Alert.alert('删除任务', '确定要删除这个任务吗？', [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          try {
            const { ok } = await apiFetch(`/tasks/${taskId}`, { method: 'DELETE' });
            if (ok) {
              await fetchTasks();
            }
          } catch (error) {
            Alert.alert('错误', '删除任务失败。');
            console.error(error);
          }
        },
      },
    ]);
  };

  const aiPlanTasks = async (prompt, maxTasks = 5) => {
    setLoading(true);

    try {
      const { ok, data } = await apiFetch('/ai/agent/run', {
        method: 'POST',
        body: {
          mode: 'text_goal',
          goal: prompt,
          max_tasks: maxTasks,
          auto_execute: true,
        },
      });

      if (!ok) {
        Alert.alert('错误', data.detail || 'AI 规划失败，请重试。');
        return;
      }

      // Agent run returns job_id for async polling
      setAiJobId(data.job_id);
    } catch (error) {
      Alert.alert('错误', 'AI 规划失败，请确认 API 已启动。');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const aiPlanImageTasks = async ({
    imageBase64,
    imageMimeType,
    filename,
    notes,
    maxTasks = 5,
  }) => {
    setImagePlanningLoading(true);

    try {
      const { ok, data } = await apiFetch('/ai/plan-image/async', {
        method: 'POST',
        body: {
          image_base64: imageBase64,
          image_mime_type: imageMimeType,
          filename,
          notes,
          max_tasks: maxTasks,
          auto_create: false,
        },
      });

      if (!ok) {
        Alert.alert('错误', data.error || data.detail || '图片解析失败，请重试。');
        return null;
      }

      return data;
    } catch (error) {
      Alert.alert('错误', '图片解析失败，请确认 API 已启动。');
      console.error(error);
      return null;
    } finally {
      setImagePlanningLoading(false);
    }
  };

  useEffect(() => {
    if (!aiJobId) {
      return undefined;
    }

    let attempts = 0;
    const MAX_ATTEMPTS = 30; // 60 秒超时

    const timer = setInterval(async () => {
      attempts += 1;
      try {
        const { ok, data: job } = await apiFetch(`/ai/agent/runs/${aiJobId}`);

        if (!ok) {
          if (attempts >= MAX_ATTEMPTS) {
            setAiJobId(null);
            Alert.alert('连接失败', '无法检查 AI 任务状态，请确认 API 已启动。');
          }
          return;
        }

        if (job.status === 'completed') {
          setAiJobId(null);
          await fetchTasks();
        } else if (job.status === 'failed') {
          setAiJobId(null);
          Alert.alert('AI 解析失败', job.error || 'AI 任务解析未能完成，请重试。');
        } else if (attempts >= MAX_ATTEMPTS) {
          setAiJobId(null);
          Alert.alert('超时', 'AI 任务解析超时，请检查 API 状态后重试。');
        }
      } catch (error) {
        console.error('Failed to check AI job status:', error);
        if (attempts >= MAX_ATTEMPTS) {
          setAiJobId(null);
          Alert.alert('连接失败', '无法检查 AI 任务状态，请确认 API 已启动。');
        }
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [aiJobId, fetchTasks]);

  return {
    tasks,
    loading,
    imagePlanningLoading,
    aiJobId,
    fetchTasks,
    createTask,
    createTasksFromCandidates,
    updateTask,
    toggleTaskCompletion,
    deleteTask,
    aiPlanTasks,
    aiPlanImageTasks,
  };
};
