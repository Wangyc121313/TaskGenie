import React, { createContext, useContext, useState } from 'react';

// 简化的任务标签和颜色配置
export const TASK_TAGS = {
  '今日': '今日',
  '明日': '明日',
  '重要': '重要',
  '已完成': '已完成',
  '已过期': '已过期',
};

export const TAG_COLORS = {
  '今日': '#6366F1',
  '明日': '#2ecc71',
  '重要': '#e74c3c',
  '已完成': '#95a5a6',
  '已过期': '#e67e22',
};

// API 配置统一由 src/utils/config.js 管理；此处重新导出以保持向后兼容
export { API_URL } from '../utils/config';

const TaskContext = createContext();

export const useTask = () => {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error('useTask must be used within a TaskProvider');
  }
  return context;
};

export const TaskProvider = ({ children }) => {
  // 改为数组，支持多选标签
  const [selectedTags, setSelectedTags] = useState([]); // 默认不筛选，显示全部任务
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  
  // 简化的新任务状态
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    priority: 'medium',
    due_date: '',
    estimated_hours: '',
  });

  const resetNewTask = () => {
    setNewTask({
      name: '',
      description: '',
      priority: 'medium',
      due_date: '',
      estimated_hours: '',
    });
  };

  // 切换标签选择状态
  const toggleTag = (tag) => {
    setSelectedTags(prevTags => {
      if (prevTags.includes(tag)) {
        // 如果已选中，则取消选择
        return prevTags.filter(t => t !== tag);
      } else {
        // 如果未选中，则添加选择
        return [...prevTags, tag];
      }
    });
  };

  const value = {
    selectedTags,
    setSelectedTags,
    toggleTag,
    editModalVisible,
    setEditModalVisible,
    createModalVisible,
    setCreateModalVisible,
    editingTask,
    setEditingTask,
    newTask,
    setNewTask,
    resetNewTask,
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
};