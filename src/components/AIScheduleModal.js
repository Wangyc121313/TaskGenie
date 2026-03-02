import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { API_URL, TAG_COLORS } from '../context/TaskContext';

const { height: screenHeight } = Dimensions.get('window');

const AIScheduleModal = ({ visible, onClose, selectedDate, onRefresh, forceRegenerate = false }) => {
  const [loading, setLoading] = useState(false);
  const [aiJobId, setAiJobId] = useState(null);
  const [scheduleResult, setScheduleResult] = useState(null);
  const [dayPreview, setDayPreview] = useState(null);

  useEffect(() => {
    if (visible && selectedDate) {
      fetchDayPreview();
      setScheduleResult(null);
      setAiJobId(null);
    }
  }, [visible, selectedDate]);

  // 获取日期预览信息
  const fetchDayPreview = async () => {
    try {
      const response = await fetch(`${API_URL}/ai/schedule-day/${selectedDate.date}`);
      const data = await response.json();
      setDayPreview(data);
    } catch (error) {
      console.error('获取日期预览失败', error);
    }
  };

  // 开始AI安排
  const handleStartSchedule = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/ai/schedule-day/async?force_regenerate=${forceRegenerate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: selectedDate.date,
          task_ids: null // 安排所有任务
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAiJobId(data.job_id);
        // 移除了 Alert.alert('处理中', 'AI 正在为您安排日程，请稍候...');
        console.log('🤖 AI日程安排已启动:', data.job_id); // 改为控制台日志
      } else {
        const error = await response.json();
        Alert.alert('错误', error.detail || 'AI 处理失败');
      }
    } catch (error) {
      Alert.alert('错误', 'AI 安排失败，请检查网络连接');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 检查AI任务状态 - 移除完成弹窗
  useEffect(() => {
    if (aiJobId) {
      const checkJobStatus = setInterval(async () => {
        try {
          const response = await fetch(`${API_URL}/ai/jobs/${aiJobId}`);
          const job = await response.json();
          
          if (job.status === 'completed') {
            setAiJobId(null);
            setScheduleResult(job.result);
            if (onRefresh) {
              onRefresh(); // 刷新父组件的数据
            }
            // 移除了 Alert.alert('成功', 'AI 已为您安排好日程');
            console.log('✅ AI日程安排完成'); // 改为控制台日志
          } else if (job.status === 'failed') {
            setAiJobId(null);
            Alert.alert('错误', job.error || 'AI 处理失败');
          }
        } catch (error) {
          console.error('检查任务状态失败', error);
        }
      }, 2000);

      return () => clearInterval(checkJobStatus);
    }
  }, [aiJobId]);

  const getPriorityColor = (priority) => {
    const colors = {
      high: '#ff4757',
      medium: '#ffa502',
      low: '#2ed573',
    };
    return colors[priority] || '#747d8c';
  };

  const getPriorityText = (priority) => {
    const texts = {
      high: '高',
      medium: '中',
      low: '低',
    };
    return texts[priority] || priority;
  };

  const formatDuration = (hours) => {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    if (h === 0) return `${m}分钟`;
    if (m === 0) return `${h}小时`;
    return `${h}小时${m}分钟`;
  };

  const C = {
    primary: '#6366F1', primaryLight: '#EEF2FF',
    surface: '#FFFFFF', surface2: '#F8FAFF',
    text1: '#0F172A', text2: '#475569', text3: '#94A3B8',
    border: '#E2E8F0', shadow: '#64748B',
    accent: '#10B981', warning: '#F59E0B',
  };

  const styles = {
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      justifyContent: 'flex-end',
    },
    modalContent: {
      backgroundColor: C.surface,
      borderTopLeftRadius: 28,
      borderTopRightRadius: 28,
      padding: 24,
      width: '100%',
      maxHeight: screenHeight * 0.92,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 20,
    },
    title: {
      fontSize: 20,
      fontWeight: '700',
      color: C.text1,
    },
    closeButton: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: C.surface2,
      justifyContent: 'center',
      alignItems: 'center',
    },
    closeButtonText: {
      fontSize: 16,
      color: C.text2,
      fontWeight: 'bold',
    },
    dateHeader: {
      backgroundColor: C.primaryLight,
      padding: 16,
      borderRadius: 14,
      marginBottom: 20,
    },
    dateText: {
      fontSize: 17,
      fontWeight: '700',
      color: C.primary,
      textAlign: 'center',
    },
    summaryContainer: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginTop: 12,
    },
    summaryItem: {
      alignItems: 'center',
    },
    summaryNumber: {
      fontSize: 18,
      fontWeight: '700',
      color: C.primary,
    },
    summaryLabel: {
      fontSize: 12,
      color: C.text3,
      marginTop: 2,
    },
    warningContainer: {
      backgroundColor: '#FEF9C3',
      padding: 12,
      borderRadius: 10,
      marginBottom: 15,
      borderLeftWidth: 4,
      borderLeftColor: C.warning,
    },
    warningText: {
      color: '#92400E',
      fontSize: 14,
    },
    startButton: {
      backgroundColor: C.primary,
      paddingVertical: 15,
      borderRadius: 14,
      alignItems: 'center',
      marginBottom: 20,
      shadowColor: C.primary,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 4,
    },
    startButtonContent: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    startButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '700',
      marginLeft: 8,
    },
    disabledButton: {
      opacity: 0.7,
    },
    scheduleContainer: {
      marginTop: 10,
    },
    scheduleHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 15,
    },
    scheduleTitle: {
      fontSize: 18,
      fontWeight: '700',
      color: C.text1,
    },
    efficiencyBadge: {
      backgroundColor: '#D1FAE5',
      paddingHorizontal: 10,
      paddingVertical: 5,
      borderRadius: 15,
    },
    efficiencyText: {
      color: '#065F46',
      fontSize: 12,
      fontWeight: 'bold',
    },
    scheduleItem: {
      backgroundColor: C.surface2,
      padding: 14,
      borderRadius: 12,
      marginBottom: 10,
      borderLeftWidth: 4,
    },
    scheduleTime: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
    },
    timeText: {
      fontSize: 15,
      fontWeight: '700',
      color: C.text1,
    },
    durationText: {
      fontSize: 12,
      color: C.text3,
    },
    taskName: {
      fontSize: 15,
      fontWeight: '600',
      color: C.text1,
      marginBottom: 5,
    },
    taskMeta: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    priorityBadge: {
      paddingHorizontal: 8,
      paddingVertical: 3,
      borderRadius: 12,
      marginRight: 8,
    },
    priorityText: {
      color: '#fff',
      fontSize: 10,
      fontWeight: 'bold',
    },
    reasonText: {
      fontSize: 13,
      color: C.text2,
      fontStyle: 'italic',
    },
    suggestionsContainer: {
      marginTop: 20,
      backgroundColor: C.primaryLight,
      padding: 15,
      borderRadius: 12,
    },
    suggestionsTitle: {
      fontSize: 15,
      fontWeight: '700',
      color: C.text1,
      marginBottom: 10,
    },
    suggestionItem: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: 8,
    },
    suggestionBullet: {
      color: C.primary,
      fontSize: 16,
      marginRight: 8,
      marginTop: 2,
    },
    suggestionText: {
      flex: 1,
      fontSize: 14,
      color: C.text2,
      lineHeight: 20,
    },
    totalHoursContainer: {
      backgroundColor: C.surface2,
      padding: 12,
      borderRadius: 10,
      marginBottom: 15,
      alignItems: 'center',
    },
    totalHoursText: {
      fontSize: 14,
      color: C.text1,
    },
    scrollContent: {
      maxHeight: screenHeight * 0.6,
    },
    noTasksContainer: {
      alignItems: 'center',
      paddingVertical: 40,
    },
    noTasksText: {
      fontSize: 16,
      color: C.text3,
      textAlign: 'center',
    },
    // 添加处理中状态的样式
    processingContainer: {
      alignItems: 'center',
      paddingVertical: 20,
    },
    processingText: {
      color: C.primary,
      fontSize: 14,
      textAlign: 'center',
      marginTop: 10,
    },
  };

  if (!visible || !selectedDate) return null;

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <Text style={styles.title}>AI 日程安排</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.dateHeader}>
            <Text style={styles.dateText}>
              {new Date(selectedDate.date).toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric',
                weekday: 'long'
              })}
            </Text>
            {dayPreview && (
              <View style={styles.summaryContainer}>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryNumber}>{dayPreview.task_count}</Text>
                  <Text style={styles.summaryLabel}>个任务</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryNumber}>{formatDuration(dayPreview.total_estimated_hours)}</Text>
                  <Text style={styles.summaryLabel}>预计用时</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryNumber}>{dayPreview.high_priority_count}</Text>
                  <Text style={styles.summaryLabel}>高优先级</Text>
                </View>
              </View>
            )}
          </View>

          <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {dayPreview && dayPreview.task_count === 0 ? (
              <View style={styles.noTasksContainer}>
                <Text style={styles.noTasksText}>
                  这一天暂无任务需要安排{'\n'}可以休息或处理其他事务
                </Text>
              </View>
            ) : (
              <>
                {dayPreview && dayPreview.overdue_count > 0 && (
                  <View style={styles.warningContainer}>
                    <Text style={styles.warningText}>
                      ⚠️ 有 {dayPreview.overdue_count} 个逾期任务需要优先处理
                    </Text>
                  </View>
                )}

                {!scheduleResult && !aiJobId ? (
                  <TouchableOpacity
                    style={[styles.startButton, (loading || aiJobId) && styles.disabledButton]}
                    onPress={handleStartSchedule}
                    disabled={loading || !!aiJobId || !dayPreview || dayPreview.task_count === 0}
                  >
                    {loading ? (
                      <View style={styles.startButtonContent}>
                        <ActivityIndicator color="#fff" />
                        <Text style={styles.startButtonText}>AI 正在规划中...</Text>
                      </View>
                    ) : (
                      <Text style={styles.startButtonText}>🤖 开始 AI 安排</Text>
                    )}
                  </TouchableOpacity>
                ) : aiJobId && !scheduleResult ? (
                  // 处理中状态显示
                  <View style={styles.processingContainer}>
                    <ActivityIndicator size="large" color="#6366F1" />
                    <Text style={styles.processingText}>
                      🤖 AI 正在为您智能安排日程...{'\n'}
                      ✨ 完成后结果会自动显示{'\n'}
                      📝 您可以关闭此窗口继续使用其他功能
                    </Text>
                  </View>
                ) : scheduleResult ? (
                  <View style={styles.scheduleContainer}>
                    <View style={styles.scheduleHeader}>
                      <Text style={styles.scheduleTitle}>📅 AI 安排结果</Text>
                      <View style={styles.efficiencyBadge}>
                        <Text style={styles.efficiencyText}>
                          效率评分: {scheduleResult.schedule.efficiency_score}/10
                        </Text>
                      </View>
                    </View>

                    <View style={styles.totalHoursContainer}>
                      <Text style={styles.totalHoursText}>
                        总用时: {formatDuration(scheduleResult.schedule.total_hours)} | 
                        任务数: {scheduleResult.schedule.schedule_items.length}
                      </Text>
                    </View>

                    {scheduleResult.schedule.schedule_items.map((item, index) => (
                      <View 
                        key={index} 
                        style={[
                          styles.scheduleItem,
                          { borderLeftColor: getPriorityColor(item.priority) }
                        ]}
                      >
                        <View style={styles.scheduleTime}>
                          <Text style={styles.timeText}>
                            {item.start_time} - {item.end_time}
                          </Text>
                          <Text style={styles.durationText}>
                            {formatDuration(item.duration)}
                          </Text>
                        </View>
                        
                        <Text style={styles.taskName}>{item.task_name}</Text>
                        
                        <View style={styles.taskMeta}>
                          <View style={[
                            styles.priorityBadge,
                            { backgroundColor: getPriorityColor(item.priority) }
                          ]}>
                            <Text style={styles.priorityText}>
                              {getPriorityText(item.priority)}优先级
                            </Text>
                          </View>
                        </View>
                        
                        <Text style={styles.reasonText}>💡 {item.reason}</Text>
                      </View>
                    ))}

                    {scheduleResult.schedule.suggestions && scheduleResult.schedule.suggestions.length > 0 && (
                      <View style={styles.suggestionsContainer}>
                        <Text style={styles.suggestionsTitle}>💡 AI 建议</Text>
                        {scheduleResult.schedule.suggestions.map((suggestion, index) => (
                          <View key={index} style={styles.suggestionItem}>
                            <Text style={styles.suggestionBullet}>•</Text>
                            <Text style={styles.suggestionText}>{suggestion}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                ) : null}
              </>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

export default AIScheduleModal;