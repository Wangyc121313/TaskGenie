import React, { useCallback, useEffect, useState } from 'react';
import {
  Modal,
  RefreshControl,
  ScrollView,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { useTask } from '../context/TaskContext';
import { TASK_TAGS } from '../context/TaskContext';
import { formatDateTime } from '../utils/dateUtils';
import { styles } from '../styles/ComponentStyles';
import SwipeableTaskItem from './SwipeableTaskItem';
import TagFilter from './TagFilter';
import TaskModal from './TaskModal';


const COLORS = {
  primary: '#6366F1',
  primaryLight: '#EEF2FF',
  aiText: '#F3E8FF',
  aiImage: '#E0F2FE',
  surface: '#FFFFFF',
  surface2: '#F8FAFF',
  text1: '#0F172A',
  text2: '#475569',
  text3: '#94A3B8',
  border: '#E2E8F0',
};


const TaskListTab = ({
  tasks,
  onCreateTask,
  onUpdateTask,
  onDeleteTask,
  onOpenAIModal,
  onOpenAIImageModal,
  pullUpPanResponder,
}) => {
  const {
    selectedTags,
    toggleTag,
    editModalVisible,
    setEditModalVisible,
    createModalVisible,
    setCreateModalVisible,
    setEditingTask,
  } = useTask();

  const [filteredTasks, setFilteredTasks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [actionSheetVisible, setActionSheetVisible] = useState(false);
  const tagValues = Object.values(TASK_TAGS);
  const todayTag = tagValues[0];
  const tomorrowTag = tagValues[1];
  const importantTag = tagValues[2];
  const completedTag = tagValues[3];
  const overdueTag = tagValues[4];

  const calculateTaskTags = useCallback(task => {
    const tags = [];
    const now = new Date();
    const today = now.toDateString();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (task.completed) {
      return [completedTag];
    }

    if (task.due_date) {
      const dueDate = new Date(task.due_date);
      const dueDateStr = dueDate.toDateString();

      if (dueDate < now) {
        tags.push(overdueTag);
      } else if (dueDateStr === today) {
        tags.push(todayTag);
      } else if (dueDateStr === tomorrow.toDateString()) {
        tags.push(tomorrowTag);
      }
    } else {
      tags.push(todayTag);
    }

    if (task.priority === 'high') {
      tags.push(importantTag);
    }

    return tags;
  }, [completedTag, overdueTag, todayTag, tomorrowTag, importantTag]);

  useEffect(() => {
    if (!selectedTags.length) {
      setFilteredTasks(tasks);
      return;
    }

    const filtered = tasks.filter(task => {
      const taskTags = calculateTaskTags(task);
      return selectedTags.every(selectedTag => taskTags.includes(selectedTag));
    });
    setFilteredTasks(filtered);
  }, [selectedTags, tasks, calculateTaskTags]);

  const onRefresh = async () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 900);
  };

  const toggleTask = async (taskId, currentStatus) => {
    await onUpdateTask(taskId, { completed: !currentStatus });
  };

  const handleEdit = task => {
    setEditingTask({ ...task });
    setEditModalVisible(true);
  };

  const handleOpenCreate = () => setActionSheetVisible(true);

  const handleManualAdd = () => {
    setActionSheetVisible(false);
    setCreateModalVisible(true);
  };

  const handleAIPlan = () => {
    setActionSheetVisible(false);
    onOpenAIModal();
  };

  const handleAIImagePlan = () => {
    setActionSheetVisible(false);
    onOpenAIImageModal();
  };

  const getEmptyStateText = () => {
    if (!tasks.length) {
      return {
        title: '暂无任务',
        hint: '点击右上角 + 可手动添加或用 AI 生成任务',
      };
    }
    if (!filteredTasks.length) {
      return {
        title: '没有符合条件的任务',
        hint: '尝试减少标签筛选或创建新任务',
      };
    }
    return {
      title: '没有符合条件的任务',
      hint: '尝试减少标签筛选或创建新任务',
    };
  };

  const emptyState = getEmptyStateText();

  return (
    <>
      <View style={listStyles.header}>
        <Text style={listStyles.headerTitle}>我的任务</Text>
        <TouchableOpacity style={listStyles.addButton} onPress={handleOpenCreate}>
          <Text style={listStyles.addButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      <TagFilter
        tasks={tasks}
        selectedTags={selectedTags}
        onTagToggle={toggleTag}
      />

      <ScrollView
        style={styles.taskList}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={COLORS.primary}
            title="刷新中"
            titleColor={COLORS.primary}
          />
        }
        {...pullUpPanResponder.panHandlers}
      >
        {filteredTasks.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>{emptyState.title}</Text>
            <Text style={styles.emptyHint}>{emptyState.hint}</Text>
          </View>
        ) : (
          filteredTasks.map(task => (
            <SwipeableTaskItem
              key={task.id}
              task={task}
              onEdit={handleEdit}
              onDelete={onDeleteTask}
              onToggle={toggleTask}
              formatDateTime={formatDateTime}
            />
          ))
        )}
      </ScrollView>

      <Modal
        transparent
        animationType="fade"
        visible={actionSheetVisible}
        onRequestClose={() => setActionSheetVisible(false)}
      >
        <TouchableOpacity
          style={listStyles.sheetOverlay}
          activeOpacity={1}
          onPress={() => setActionSheetVisible(false)}
        >
          <TouchableOpacity activeOpacity={1} onPress={() => {}}>
            <View style={listStyles.sheet}>
              <Text style={listStyles.sheetTitle}>创建任务</Text>
              <Text style={listStyles.sheetSubtitle}>选择创建任务的方式。</Text>

              <TouchableOpacity style={listStyles.sheetOption} onPress={handleManualAdd}>
                <View
                  style={[
                    listStyles.sheetOptionIcon,
                    { backgroundColor: COLORS.primaryLight },
                  ]}
                >
                  <Text style={listStyles.sheetOptionEmoji}>+</Text>
                </View>
                <View style={listStyles.sheetOptionBody}>
                  <Text style={listStyles.sheetOptionTitle}>手动创建</Text>
                  <Text style={listStyles.sheetOptionDesc}>
                    填写标题、优先级、截止时间等信息创建任务。
                  </Text>
                </View>
              </TouchableOpacity>

              <View style={listStyles.sheetDivider} />

              <TouchableOpacity style={listStyles.sheetOption} onPress={handleAIPlan}>
                <View
                  style={[
                    listStyles.sheetOptionIcon,
                    listStyles.aiTextOptionIcon,
                  ]}
                >
                  <Text style={listStyles.sheetOptionEmoji}>AI</Text>
                </View>
                <View style={listStyles.sheetOptionBody}>
                  <Text style={listStyles.sheetOptionTitle}>文字生成任务</Text>
                  <Text style={listStyles.sheetOptionDesc}>
                    描述目标，AI 为你拆解成可执行步骤。
                  </Text>
                </View>
              </TouchableOpacity>

              <View style={listStyles.sheetDivider} />

              <TouchableOpacity style={listStyles.sheetOption} onPress={handleAIImagePlan}>
                <View
                  style={[
                    listStyles.sheetOptionIcon,
                    listStyles.aiImageOptionIcon,
                  ]}
                >
                  <Text style={listStyles.sheetOptionEmoji}>IMG</Text>
                </View>
                <View style={listStyles.sheetOptionBody}>
                  <Text style={listStyles.sheetOptionTitle}>图片生成任务</Text>
                  <Text style={listStyles.sheetOptionDesc}>
                    从截图、白板、手写笔记中提取任务。
                  </Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                style={listStyles.sheetCancel}
                onPress={() => setActionSheetVisible(false)}
              >
                <Text style={listStyles.sheetCancelText}>取消</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>

      <TaskModal
        visible={createModalVisible || editModalVisible}
        isEdit={editModalVisible}
        onClose={() => {
          setCreateModalVisible(false);
          setEditModalVisible(false);
        }}
        onSave={editModalVisible ? onUpdateTask : onCreateTask}
      />
    </>
  );
};


const listStyles = {
  header: {
    backgroundColor: COLORS.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  addButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.22)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '400',
    lineHeight: 22,
  },
  sheetOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.55)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 36,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text1,
    marginBottom: 4,
  },
  sheetSubtitle: {
    fontSize: 13,
    color: COLORS.text3,
    marginBottom: 20,
  },
  sheetOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
  },
  sheetOptionIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  sheetOptionEmoji: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.text1,
  },
  sheetOptionBody: {
    flex: 1,
  },
  aiTextOptionIcon: {
    backgroundColor: COLORS.aiText,
  },
  aiImageOptionIcon: {
    backgroundColor: COLORS.aiImage,
  },
  sheetOptionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text1,
    marginBottom: 3,
  },
  sheetOptionDesc: {
    fontSize: 13,
    color: COLORS.text2,
    lineHeight: 18,
  },
  sheetDivider: {
    height: 1,
    backgroundColor: COLORS.border,
  },
  sheetCancel: {
    marginTop: 18,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: COLORS.surface2,
    alignItems: 'center',
  },
  sheetCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text2,
  },
};


export default TaskListTab;
