import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { useVoiceInput } from '../hooks/useVoiceInput';

const { height: screenHeight } = Dimensions.get('window');

const AIPlanningModal = ({ visible, onClose, onPlan, loading, aiJobId }) => {
  const [aiPrompt, setAiPrompt] = useState('');
  const [maxTasks, setMaxTasks] = useState(5); // 默认5个任务

  const { listening, toggle: toggleVoice, error: voiceError, available: voiceAvailable } =
    useVoiceInput({ onResult: (text) => setAiPrompt(text) });

  useEffect(() => {
    if (!visible) {
      setAiPrompt('');
      setMaxTasks(5); // 重置为默认值
    }
  }, [visible]);

  const handlePlan = () => {
    if (!aiPrompt.trim()) {
      Alert.alert('提示', '请输入任务描述');
      return;
    }
    
    if (maxTasks < 1 || maxTasks > 10) {
      Alert.alert('提示', '任务数量应该在1-10之间');
      return;
    }
    
    onPlan(aiPrompt, maxTasks);
    onClose(); // 提交后立即关闭弹窗，后台轮询任务状态
  };

  const handleMaxTasksChange = (text) => {
    const num = parseInt(text);
    if (isNaN(num)) {
      setMaxTasks('');
    } else {
      setMaxTasks(Math.max(1, Math.min(10, num))); // 限制在1-10之间
    }
  };

  const C = {
    primary: '#6366F1', primaryLight: '#EEF2FF',
    surface: '#FFFFFF', surface2: '#F8FAFF',
    text1: '#0F172A', text2: '#475569', text3: '#94A3B8',
    border: '#E2E8F0', shadow: '#64748B',
  };

  const styles = {
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      justifyContent: 'flex-end',
    },
    aiModalContent: {
      backgroundColor: C.surface,
      borderTopLeftRadius: 28,
      borderTopRightRadius: 28,
      padding: 24,
      width: '100%',
      maxHeight: screenHeight * 0.88,
    },
    aiHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 16,
    },
    aiTitle: {
      fontSize: 20,
      fontWeight: '700',
      color: C.text1,
    },
    aiCloseButton: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: C.surface2,
      justifyContent: 'center',
      alignItems: 'center',
    },
    aiCloseButtonText: {
      fontSize: 16,
      color: C.text2,
      fontWeight: 'bold',
    },
    aiHint: {
      fontSize: 14,
      color: C.text2,
      lineHeight: 20,
      marginBottom: 20,
    },
    aiInput: {
      borderWidth: 1.5,
      borderColor: C.border,
      borderRadius: 14,
      padding: 14,
      fontSize: 15,
      backgroundColor: C.surface,
      minHeight: 120,
      marginBottom: 20,
      textAlignVertical: 'top',
    },
    settingsContainer: {
      backgroundColor: C.surface2,
      padding: 15,
      borderRadius: 14,
      marginBottom: 20,
    },
    settingsTitle: {
      fontSize: 15,
      fontWeight: '700',
      color: C.text1,
      marginBottom: 12,
    },
    settingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    settingLabel: {
      fontSize: 14,
      color: C.text2,
      flex: 1,
    },
    taskCountContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    taskCountButton: {
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: C.primary,
      justifyContent: 'center',
      alignItems: 'center',
      marginHorizontal: 8,
    },
    taskCountButtonText: {
      color: '#fff',
      fontSize: 18,
      fontWeight: 'bold',
    },
    taskCountInput: {
      width: 50,
      height: 36,
      borderWidth: 1.5,
      borderColor: C.border,
      borderRadius: 10,
      textAlign: 'center',
      fontSize: 16,
      backgroundColor: C.surface,
    },
    exampleContainer: {
      backgroundColor: C.primaryLight,
      padding: 14,
      borderRadius: 12,
      marginBottom: 20,
    },
    exampleTitle: {
      fontSize: 14,
      fontWeight: '700',
      color: C.primary,
      marginBottom: 8,
    },
    exampleText: {
      fontSize: 13,
      color: C.text2,
      lineHeight: 18,
    },
    aiButton: {
      backgroundColor: C.primary,
      paddingVertical: 15,
      borderRadius: 14,
      alignItems: 'center',
      shadowColor: C.primary,
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 8,
      elevation: 4,
    },
    aiButtonContent: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    aiButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '700',
      marginLeft: 8,
    },
    disabledButton: {
      opacity: 0.7,
    },
    voiceRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 16,
      gap: 8,
    },
    voiceButton: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      paddingVertical: 10,
      paddingHorizontal: 14,
      borderRadius: 12,
      backgroundColor: '#F0FDF4',
      borderWidth: 1.5,
      borderColor: '#86EFAC',
    },
    voiceButtonListening: {
      backgroundColor: '#FEF2F2',
      borderColor: '#FCA5A5',
    },
    voiceButtonText: {
      fontSize: 13,
      fontWeight: '600',
      color: '#16A34A',
      marginLeft: 6,
    },
    voiceButtonTextListening: {
      color: '#DC2626',
    },
    voiceErrorText: {
      fontSize: 12,
      color: '#EF4444',
      marginBottom: 8,
      textAlign: 'center',
    },
    processingContainer: {
      marginTop: 20,
      alignItems: 'center',
    },
    processingText: {
      color: C.primary,
      fontSize: 14,
      textAlign: 'center',
      lineHeight: 20,
    },
  };

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.aiModalContent}>
          <View style={styles.aiHeader}>
            <Text style={styles.aiTitle}>🤖 AI 任务规划助手</Text>
            <TouchableOpacity onPress={onClose} style={styles.aiCloseButton}>
              <Text style={styles.aiCloseButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <Text style={styles.aiHint}>
            描述你想要完成的目标，AI 会帮你分解成具体的、可执行的任务步骤
          </Text>
          
          <TextInput
            style={[styles.aiInput, listening && { borderColor: '#FCA5A5' }]}
            placeholder="例如：准备一场生日派对、学习React Native、写一份项目报告..."
            value={listening ? '🎙️ 正在聆听，请说话...' : aiPrompt}
            onChangeText={listening ? undefined : setAiPrompt}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            editable={!listening}
          />

          {/* 语音输入 */}
          {voiceAvailable && (
            <View style={styles.voiceRow}>
              <TouchableOpacity
                style={[styles.voiceButton, listening && styles.voiceButtonListening]}
                onPress={toggleVoice}
                activeOpacity={0.75}
              >
                <Text style={{ fontSize: 16 }}>{listening ? '🔴' : '🎤'}</Text>
                <Text style={[styles.voiceButtonText, listening && styles.voiceButtonTextListening]}>
                  {listening ? '点击停止' : '语音输入'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
          {voiceError ? <Text style={styles.voiceErrorText}>{voiceError}</Text> : null}

          {/* 任务设置 */}
          <View style={styles.settingsContainer}>
            <Text style={styles.settingsTitle}>⚙️ 分解设置</Text>
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>分解任务数量：</Text>
              <View style={styles.taskCountContainer}>
                <TouchableOpacity
                  style={styles.taskCountButton}
                  onPress={() => setMaxTasks(Math.max(1, maxTasks - 1))}
                >
                  <Text style={styles.taskCountButtonText}>−</Text>
                </TouchableOpacity>
                
                <TextInput
                  style={styles.taskCountInput}
                  value={maxTasks.toString()}
                  onChangeText={handleMaxTasksChange}
                  keyboardType="numeric"
                  maxLength={2}
                />
                
                <TouchableOpacity
                  style={styles.taskCountButton}
                  onPress={() => setMaxTasks(Math.min(10, maxTasks + 1))}
                >
                  <Text style={styles.taskCountButtonText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* 示例提示 */}
          <View style={styles.exampleContainer}>
            <Text style={styles.exampleTitle}>💡 输入示例</Text>
            <Text style={styles.exampleText}>
              输入："学习React Native开发"
              {'\n'}分解为：
              {'\n'}• React Native学习计划 Step1：搭建开发环境
              {'\n'}• React Native学习计划 Step2：学习基础组件
              {'\n'}• React Native学习计划 Step3：制作第一个应用
            </Text>
          </View>
          
          <TouchableOpacity
            style={[styles.aiButton, (loading || aiJobId) && styles.disabledButton]}
            onPress={handlePlan}
            disabled={loading || !!aiJobId}
          >
            {loading || aiJobId ? (
              <View style={styles.aiButtonContent}>
                <ActivityIndicator color="#fff" />
                <Text style={styles.aiButtonText}>AI 正在思考中...</Text>
              </View>
            ) : (
              <Text style={styles.aiButtonText}>🚀 开始 AI 规划</Text>
            )}
          </TouchableOpacity>
          
        </View>
      </View>
    </Modal>
  );
};

export default AIPlanningModal;