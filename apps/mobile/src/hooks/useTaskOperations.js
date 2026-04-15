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
        return false;
      }

      if (refresh) {
        await fetchTasks();
      }
      if (showAlert) {
        Alert.alert('Success', 'Task created.');
      }
      return true;
    } catch (error) {
      Alert.alert('Error', 'Failed to create task.');
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
        return false;
      }

      await fetchTasks();
      return true;
    } catch (error) {
      Alert.alert('Error', 'Failed to update task.');
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
      Alert.alert('Error', 'Failed to update task status.');
      console.error(error);
      await fetchTasks();
      return false;
    }
  };

  const deleteTask = async taskId => {
    Alert.alert('Delete Task', 'Delete this task?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
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
            Alert.alert('Error', 'Failed to delete task.');
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
        Alert.alert('Error', error.detail || 'AI planning failed.');
        return;
      }

      const data = await response.json();
      setAiJobId(data.job_id);
      Alert.alert(
        'Planning',
        `The AI planner is generating up to ${maxTasks} tasks for you.`,
      );
    } catch (error) {
      Alert.alert('Error', 'AI planning failed.');
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
        Alert.alert('Error', data.error || data.detail || 'Image planning failed.');
        return null;
      }

      return data;
    } catch (error) {
      Alert.alert('Error', 'Image planning failed.');
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

    const timer = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/ai/jobs/${aiJobId}`);
        const job = await response.json();

        if (job.status === 'completed') {
          setAiJobId(null);
          await fetchTasks();
        } else if (job.status === 'failed') {
          setAiJobId(null);
          Alert.alert('Error', job.error || 'AI processing failed.');
        }
      } catch (error) {
        console.error('Failed to check AI job status:', error);
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
