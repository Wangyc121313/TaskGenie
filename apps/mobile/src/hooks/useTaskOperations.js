import { useCallback, useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { API_URL } from '../context/TaskContext';


export const useTaskOperations = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [imagePlanningLoading, setImagePlanningLoading] = useState(false);
  const [aiJobId, setAiJobId] = useState(null);

  const fetchTasks = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/tasks`);
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load tasks.');
      console.error(error);
    }
  }, []);

  const createTask = async (taskData, options = {}) => {
    const { refresh = true, showAlert = false } = options;
    try {
      const response = await fetch(`${API_URL}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        Alert.alert('错误', errData.detail || '创建任务失败，请检查输入并重试');
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

      const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
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
      const response = await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completed: !currentCompleted,
        }),
      });

      if (!response.ok) {
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
            const response = await fetch(`${API_URL}/tasks/${taskId}`, {
              method: 'DELETE',
            });

            if (response.ok) {
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
      const response = await fetch(`${API_URL}/ai/plan-tasks/async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          max_tasks: maxTasks,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        Alert.alert('错误', error.detail || 'AI 规划失败，请重试。');
        return;
      }

      const data = await response.json();
      setAiJobId(data.job_id);
      Alert.alert(
        'AI 规划中',
        `AI 正在为你生成最多 ${maxTasks} 个任务，请稍候。`,
      );
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
      const response = await fetch(`${API_URL}/ai/plan-image/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: imageBase64,
          image_mime_type: imageMimeType,
          filename,
          notes,
          max_tasks: maxTasks,
          auto_create: false,
        }),
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
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
        const response = await fetch(`${API_URL}/ai/jobs/${aiJobId}`);
        const job = await response.json();

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
