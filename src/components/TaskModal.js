import React from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { useTask } from '../context/TaskContext';

const TaskModal = ({ visible, isEdit, onClose, onSave }) => {
  const {
    editingTask,
    setEditingTask,
    newTask,
    setNewTask,
    resetNewTask,
  } = useTask();

  const currentTask = isEdit ? editingTask : newTask;
  const setCurrentTask = isEdit ? setEditingTask : setNewTask;

  const handleSave = async () => {
    if (!currentTask?.name?.trim()) {
      Alert.alert('提示', '请输入任务名称');
      return;
    }

    // 简化的任务数据（移除tag相关字段）
    const taskData = {
      name: currentTask.name,
      description: currentTask.description,
      priority: currentTask.priority,
      due_date: currentTask.due_date || null,
      estimated_hours: currentTask.estimated_hours ? parseFloat(currentTask.estimated_hours) : null,
    };

    let success;
    if (isEdit) {
      success = await onSave(currentTask.id, taskData);
    } else {
      success = await onSave(taskData);
    }

    if (success) {
      onClose();
      if (!isEdit) {
        resetNewTask();
      }
      Alert.alert('成功', isEdit ? '任务已更新' : '任务已创建');
    }
  };

  const getDateOptions = () => {
    const now = new Date();
    
    // 今天 18:00
    const today = new Date(now);
    today.setHours(18, 0, 0, 0);
    
    // 明天 18:00
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(18, 0, 0, 0);
    
    // 后天 18:00
    const dayAfterTomorrow = new Date(now);
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
    dayAfterTomorrow.setHours(18, 0, 0, 0);
    
    // 下周 18:00
    const nextWeek = new Date(now);
    nextWeek.setDate(nextWeek.getDate() + 7);
    nextWeek.setHours(18, 0, 0, 0);

    return [
      { 
        label: '今天晚上', 
        date: today,
        description: `今天 18:00`
      },
      { 
        label: '明天晚上', 
        date: tomorrow,
        description: `明天 18:00`
      },
      { 
        label: '后天晚上', 
        date: dayAfterTomorrow,
        description: `后天 18:00`
      },
      { 
        label: '下周', 
        date: nextWeek,
        description: `下周${['日', '一', '二', '三', '四', '五', '六'][nextWeek.getDay()]} 18:00`
      },
    ];
  };

  const handleDateSelect = (option) => {
    setCurrentTask({
      ...currentTask,
      due_date: option.date.toISOString()
    });
  };

  const clearDueDate = () => {
    setCurrentTask({
      ...currentTask,
      due_date: null
    });
  };

  const getSelectedDateLabel = () => {
    if (!currentTask?.due_date) return '选择截止时间';
    
    const selectedDate = new Date(currentTask.due_date);
    const options = getDateOptions();
    
    // 检查是否匹配预设选项
    for (const option of options) {
      if (Math.abs(selectedDate.getTime() - option.date.getTime()) < 60000) { // 1分钟内的差异
        return option.description;
      }
    }
    
    // 如果不匹配预设选项，显示具体日期时间
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth() + 1;
    const day = selectedDate.getDate();
    const hour = selectedDate.getHours();
    const minute = selectedDate.getMinutes();
    
    return `${year}-${month}-${day} ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
  };

  const styles = {
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      justifyContent: 'flex-end',
    },
    modalContent: {
      backgroundColor: '#fff',
      borderTopLeftRadius: 28,
      borderTopRightRadius: 28,
      padding: 24,
      width: '100%',
      maxHeight: '88%',
    },
    modalScroll: {
      maxHeight: 460,
    },
    modalTitle: {
      fontSize: 20,
      fontWeight: '800',
      color: '#0F172A',
      marginBottom: 22,
      textAlign: 'center',
      letterSpacing: 0.2,
    },
    inputLabel: {
      fontSize: 13,
      color: '#64748B',
      marginBottom: 6,
      marginTop: 16,
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    modalInput: {
      borderWidth: 1.5,
      borderColor: '#E2E8F0',
      borderRadius: 12,
      padding: 13,
      fontSize: 15,
      backgroundColor: '#F8FAFF',
      color: '#0F172A',
    },
    textArea: {
      minHeight: 80,
      textAlignVertical: 'top',
    },
    prioritySelector: {
      flexDirection: 'row',
      marginTop: 5,
    },
    priorityOption: {
      flex: 1,
      paddingVertical: 11,
      alignItems: 'center',
      borderWidth: 1.5,
      borderColor: '#E2E8F0',
      marginHorizontal: 4,
      borderRadius: 12,
      backgroundColor: '#F8FAFF',
    },
    selectedPriority: {
      backgroundColor: '#6366F1',
      borderColor: '#6366F1',
    },
    priorityOptionText: {
      color: '#64748B',
      fontWeight: '600',
    },
    selectedPriorityText: {
      color: '#fff',
    },
    // 日期时间选择样式
    dateTimeContainer: {
      marginTop: 5,
    },
    currentSelection: {
      backgroundColor: '#F8FAFF',
      padding: 13,
      borderRadius: 12,
      borderWidth: 1.5,
      borderColor: '#E2E8F0',
      marginBottom: 14,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    currentSelectionText: {
      fontSize: 14,
      color: '#0F172A',
      fontWeight: '500',
    },
    currentSelectionIcon: {
      fontSize: 16,
      color: '#6366F1',
    },
    dateOptionsContainer: {
      marginBottom: 14,
    },
    dateOptionRow: {
      flexDirection: 'row',
      marginBottom: 8,
    },
    dateOption: {
      flex: 1,
      padding: 12,
      marginHorizontal: 4,
      backgroundColor: '#F8FAFF',
      borderRadius: 12,
      borderWidth: 1.5,
      borderColor: '#E2E8F0',
      alignItems: 'center',
    },
    selectedDateOption: {
      backgroundColor: '#6366F1',
      borderColor: '#6366F1',
    },
    dateOptionLabel: {
      fontSize: 13,
      color: '#0F172A',
      fontWeight: '600',
      marginBottom: 2,
    },
    selectedDateOptionLabel: {
      color: '#fff',
    },
    dateOptionDescription: {
      fontSize: 11,
      color: '#64748B',
    },
    selectedDateOptionDescription: {
      color: '#fff',
      opacity: 0.9,
    },
    clearDateButton: {
      paddingVertical: 9,
      paddingHorizontal: 14,
      backgroundColor: '#F1F5F9',
      borderRadius: 10,
      alignItems: 'center',
      marginTop: 8,
    },
    clearDateText: {
      fontSize: 12,
      color: '#64748B',
      fontWeight: '500',
    },
    modalButtons: {
      flexDirection: 'row',
      marginTop: 26,
      marginBottom: 4,
    },
    modalButton: {
      flex: 1,
      paddingVertical: 14,
      borderRadius: 14,
      alignItems: 'center',
      marginHorizontal: 5,
    },
    cancelButton: {
      backgroundColor: '#F1F5F9',
    },
    cancelButtonText: {
      color: '#64748B',
      fontWeight: '700',
    },
    saveButton: {
      backgroundColor: '#6366F1',
    },
    saveButtonText: {
      color: '#fff',
      fontWeight: '700',
    },
  };

  const dateOptions = getDateOptions();

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>
            {isEdit ? '编辑任务' : '创建新任务'}
          </Text>
          
          <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.inputLabel}>任务名称 {!isEdit && '*'}</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="输入任务名称"
              value={currentTask?.name || ''}
              onChangeText={(text) => setCurrentTask({...currentTask, name: text})}
            />
            
            <Text style={styles.inputLabel}>描述</Text>
            <TextInput
              style={[styles.modalInput, styles.textArea]}
              placeholder="详细描述任务内容"
              value={currentTask?.description || ''}
              onChangeText={(text) => setCurrentTask({...currentTask, description: text})}
              multiline
              numberOfLines={3}
            />
            
            <Text style={styles.inputLabel}>优先级</Text>
            <View style={styles.prioritySelector}>
              {['low', 'medium', 'high'].map((priority) => (
                <TouchableOpacity
                  key={priority}
                  style={[
                    styles.priorityOption,
                    currentTask?.priority === priority && styles.selectedPriority,
                  ]}
                  onPress={() => setCurrentTask({...currentTask, priority})}
                >
                  <Text style={[
                    styles.priorityOptionText,
                    currentTask?.priority === priority && styles.selectedPriorityText,
                  ]}>
                    {priority === 'high' ? '高' : priority === 'medium' ? '中' : '低'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            
            <Text style={styles.inputLabel}>截止时间</Text>
            <View style={styles.dateTimeContainer}>
              {/* 当前选择显示 */}
              <View style={styles.currentSelection}>
                <Text style={styles.currentSelectionText}>
                  {getSelectedDateLabel()}
                </Text>
                <Text style={styles.currentSelectionIcon}>📅</Text>
              </View>
              
              {/* 日期选择选项 */}
              <View style={styles.dateOptionsContainer}>
                {/* 第一行：今天、明天 */}
                <View style={styles.dateOptionRow}>
                  {dateOptions.slice(0, 2).map((option, index) => {
                    const isSelected = currentTask?.due_date && 
                      Math.abs(new Date(currentTask.due_date).getTime() - option.date.getTime()) < 60000;
                    
                    return (
                      <TouchableOpacity
                        key={index}
                        style={[
                          styles.dateOption,
                          isSelected && styles.selectedDateOption
                        ]}
                        onPress={() => handleDateSelect(option)}
                      >
                        <Text style={[
                          styles.dateOptionLabel,
                          isSelected && styles.selectedDateOptionLabel
                        ]}>
                          {option.label}
                        </Text>
                        <Text style={[
                          styles.dateOptionDescription,
                          isSelected && styles.selectedDateOptionDescription
                        ]}>
                          {option.description}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
                
                {/* 第二行：后天、下周 */}
                <View style={styles.dateOptionRow}>
                  {dateOptions.slice(2, 4).map((option, index) => {
                    const isSelected = currentTask?.due_date && 
                      Math.abs(new Date(currentTask.due_date).getTime() - option.date.getTime()) < 60000;
                    
                    return (
                      <TouchableOpacity
                        key={index + 2}
                        style={[
                          styles.dateOption,
                          isSelected && styles.selectedDateOption
                        ]}
                        onPress={() => handleDateSelect(option)}
                      >
                        <Text style={[
                          styles.dateOptionLabel,
                          isSelected && styles.selectedDateOptionLabel
                        ]}>
                          {option.label}
                        </Text>
                        <Text style={[
                          styles.dateOptionDescription,
                          isSelected && styles.selectedDateOptionDescription
                        ]}>
                          {option.description}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>

              {/* 清除截止时间按钮 */}
              {currentTask?.due_date && (
                <TouchableOpacity
                  style={styles.clearDateButton}
                  onPress={clearDueDate}
                >
                  <Text style={styles.clearDateText}>清除截止时间</Text>
                </TouchableOpacity>
              )}
            </View>
            
            <Text style={styles.inputLabel}>预计时长（小时）</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="例如: 2.5"
              value={currentTask?.estimated_hours?.toString() || ''}
              onChangeText={(text) => setCurrentTask({...currentTask, estimated_hours: text})}
              keyboardType="numeric"
            />
          </ScrollView>
          
          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.cancelButton]}
              onPress={onClose}
            >
              <Text style={styles.cancelButtonText}>取消</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.saveButton]}
              onPress={handleSave}
            >
              <Text style={styles.saveButtonText}>
                {isEdit ? '保存' : '创建'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

export default TaskModal;