import React, { useState, useEffect } from 'react';
import {
  ScrollView,
  View,
  Text,
  TouchableOpacity,
  RefreshControl,
  Modal,
} from 'react-native';
import SwipeableTaskItem from './SwipeableTaskItem';
import TaskModal from './TaskModal';
import TagFilter from './TagFilter';
import { useTask } from '../context/TaskContext';
import { formatDateTime } from '../utils/dateUtils';
import { styles } from '../styles/ComponentStyles';

const C = {
  primary: '#6366F1', primaryDark: '#4F46E5', primaryLight: '#EEF2FF',
  surface: '#FFFFFF', surface2: '#F8FAFF',
  text1: '#0F172A', text2: '#475569', text3: '#94A3B8',
  border: '#E2E8F0',
};

const TaskListTab = ({ 
  tasks, 
  onCreateTask, 
  onUpdateTask, 
  onDeleteTask, 
  onOpenAIModal,
  pullUpPanResponder 
}) => {
  const {
    selectedTags,
    toggleTag,
    editModalVisible,
    setEditModalVisible,
    createModalVisible,
    setCreateModalVisible,
    editingTask,
    setEditingTask,
  } = useTask();

  const [filteredTasks, setFilteredTasks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [actionSheetVisible, setActionSheetVisible] = useState(false);

  // 本地计算任务标签的函数（与后端逻辑保持一致）
  const calculateTaskTags = (task) => {
    const tags = [];
    const now = new Date();
    const today = now.toDateString();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (task.completed) {
      return ['已完成'];
    }
    
    if (task.due_date) {
      const dueDate = new Date(task.due_date);
      const dueDateStr = dueDate.toDateString();
      
      if (dueDate < now) {
        tags.push('已过期');
      } else if (dueDateStr === today) {
        tags.push('今日');
      } else if (dueDateStr === tomorrow.toDateString()) {
        tags.push('明日');
      }
    } else {
      tags.push('今日');
    }
    
    if (task.priority === 'high') {
      tags.push('重要');
    }
    
    return tags;
  };

  // 根据选中的标签过滤任务（AND逻辑）
  const filterTasksByTags = (tags) => {
    if (tags.length === 0) {
      setFilteredTasks(tasks);
      return;
    }
    const filtered = tasks.filter(task => {
      const taskTags = calculateTaskTags(task);
      return tags.every(selectedTag => taskTags.includes(selectedTag));
    });
    setFilteredTasks(filtered);
  };

  const handleTagToggle = (tag) => toggleTag(tag);

  useEffect(() => {
    filterTasksByTags(selectedTags);
  }, [selectedTags, tasks]);

  const onRefresh = async () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  const toggleTask = async (taskId, currentStatus) => {
    await onUpdateTask(taskId, { completed: !currentStatus });
  };

  const handleEdit = (task) => {
    setEditingTask({...task});
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

  const getEmptyStateText = () => {
    if (tasks.length === 0) {
      return { title: '暂无任务', hint: '点击右上角 ＋ 创建第一个任务' };
    } else if (selectedTags.length === 0) {
      return { title: '暂无任务', hint: '选择标签来筛选任务' };
    } else if (selectedTags.length === 1) {
      return { title: `暂无"${selectedTags[0]}"任务`, hint: '试试调整标签筛选条件' };
    } else {
      return { title: `暂无"${selectedTags.join(' + ')}"任务`, hint: '试试调整标签筛选条件' };
    }
  };

  const emptyState = getEmptyStateText();

  return (
    <>
      {/* ── 顶部标题栏 ───────────────────────────────── */}
      <View style={listStyles.header}>
        <Text style={listStyles.headerTitle}>我的任务</Text>
        <TouchableOpacity style={listStyles.addBtn} onPress={handleOpenCreate}>
          <Text style={listStyles.addBtnText}>＋</Text>
        </TouchableOpacity>
      </View>

      {/* ── 标签筛选器 ───────────────────────────────── */}
      <TagFilter
        tasks={tasks}
        selectedTags={selectedTags}
        onTagToggle={handleTagToggle}
      />

      {/* ── 任务列表 ─────────────────────────────────── */}
      <ScrollView 
        style={styles.taskList}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#6366F1"
            title="下拉刷新"
            titleColor="#6366F1"
          />
        }
        {...pullUpPanResponder.panHandlers}
      >
        {filteredTasks.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>{emptyState.title}</Text>
            <Text style={styles.emptyHint}>{emptyState.hint}</Text>
            <Text style={styles.emptyHint}>或下拉页面搜索任务</Text>
          </View>
        ) : (
          filteredTasks.map((task) => (
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

      {/* ── 新建任务选择弹窗 ──────────────────────────── */}
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
            <Text style={listStyles.sheetTitle}>创建新任务</Text>
            <Text style={listStyles.sheetSubtitle}>选择创建方式</Text>

            <TouchableOpacity style={listStyles.sheetOption} onPress={handleManualAdd}>
              <View style={[listStyles.sheetOptionIcon, { backgroundColor: C.primaryLight }]}>
                <Text style={listStyles.sheetOptionEmoji}>✏️</Text>
              </View>
              <View style={listStyles.sheetOptionBody}>
                <Text style={listStyles.sheetOptionTitle}>手动添加</Text>
                <Text style={listStyles.sheetOptionDesc}>填写任务名称、优先级、截止时间等详细信息</Text>
              </View>
              <Text style={listStyles.sheetChevron}>›</Text>
            </TouchableOpacity>

            <View style={listStyles.sheetDivider} />

            <TouchableOpacity style={listStyles.sheetOption} onPress={handleAIPlan}>
              <View style={[listStyles.sheetOptionIcon, { backgroundColor: '#F3E8FF' }]}>
                <Text style={listStyles.sheetOptionEmoji}>🤖</Text>
              </View>
              <View style={listStyles.sheetOptionBody}>
                <Text style={listStyles.sheetOptionTitle}>AI 规划</Text>
                <Text style={listStyles.sheetOptionDesc}>描述你的目标，让 AI 自动拆解成可执行的子任务</Text>
              </View>
              <Text style={listStyles.sheetChevron}>›</Text>
            </TouchableOpacity>

            <TouchableOpacity style={listStyles.sheetCancel} onPress={() => setActionSheetVisible(false)}>
              <Text style={listStyles.sheetCancelText}>取消</Text>
            </TouchableOpacity>
          </View>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>

      {/* ── 任务详情模态框 ────────────────────────────── */}
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

// 本组件专属样式
const listStyles = {
  header: {
    backgroundColor: C.primary,
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
  addBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.22)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addBtnText: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '300',
    lineHeight: 28,
    marginTop: -2,
  },
  // Action sheet
  sheetOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.55)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: C.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 36,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: C.text1,
    marginBottom: 4,
  },
  sheetSubtitle: {
    fontSize: 13,
    color: C.text3,
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
    fontSize: 22,
  },
  sheetOptionBody: {
    flex: 1,
  },
  sheetOptionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: C.text1,
    marginBottom: 3,
  },
  sheetOptionDesc: {
    fontSize: 13,
    color: C.text2,
    lineHeight: 18,
  },
  sheetChevron: {
    fontSize: 22,
    color: C.text3,
    marginLeft: 8,
  },
  sheetDivider: {
    height: 1,
    backgroundColor: C.border,
    marginVertical: 4,
  },
  sheetCancel: {
    marginTop: 16,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: C.surface2,
    alignItems: 'center',
  },
  sheetCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: C.text2,
  },
};

export default TaskListTab;