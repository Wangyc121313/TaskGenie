import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  Modal,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';


const COLORS = {
  primary: '#6366F1',
  primaryLight: '#EEF2FF',
  success: '#10B981',
  warning: '#F59E0B',
  surface: '#FFFFFF',
  surface2: '#F8FAFF',
  border: '#E2E8F0',
  text1: '#0F172A',
  text2: '#475569',
  text3: '#94A3B8',
};


const AIImagePlanningModal = ({
  visible,
  onClose,
  onAnalyzeImage,
  onCreateTasks,
  loading,
}) => {
  const [imageAsset, setImageAsset] = useState(null);
  const [notes, setNotes] = useState('');
  const [maxTasks, setMaxTasks] = useState(5);
  const [result, setResult] = useState(null);
  const [selectedCandidates, setSelectedCandidates] = useState({});
  const [submittingTasks, setSubmittingTasks] = useState(false);

  useEffect(() => {
    if (!visible) {
      setImageAsset(null);
      setNotes('');
      setMaxTasks(5);
      setResult(null);
      setSelectedCandidates({});
      setSubmittingTasks(false);
    }
  }, [visible]);

  const selectedTaskCandidates = useMemo(() => {
    if (!result?.task_candidates?.length) {
      return [];
    }
    return result.task_candidates.filter((_, index) => selectedCandidates[index] !== false);
  }, [result, selectedCandidates]);

  const handlePickImage = async () => {
    const pickerResult = await launchImageLibrary({
      mediaType: 'photo',
      selectionLimit: 1,
      includeBase64: true,
      quality: 0.8,
    });

    if (pickerResult.didCancel) {
      return;
    }
    if (pickerResult.errorCode) {
      Alert.alert('图片错误', pickerResult.errorMessage || '选择图片失败，请重试。');
      return;
    }

    const asset = pickerResult.assets?.[0];
    if (!asset?.base64 || !asset?.type) {
      Alert.alert('图片错误', '所选图片不包含可用的图像数据，请重新选择。');
      return;
    }

    setImageAsset(asset);
    setResult(null);
    setSelectedCandidates({});
  };

  const handleAnalyze = async () => {
    if (!imageAsset?.base64 || !imageAsset?.type) {
      Alert.alert('请先选择图片', '运行分析前请先选择一张图片。');
      return;
    }

    const response = await onAnalyzeImage({
      imageBase64: imageAsset.base64,
      imageMimeType: imageAsset.type,
      filename: imageAsset.fileName || 'selected-image',
      notes,
      maxTasks,
    });

    if (!response) {
      return;
    }

    setResult(response);
    const initialSelection = {};
    (response.task_candidates || []).forEach((_, index) => {
      initialSelection[index] = true;
    });
    setSelectedCandidates(initialSelection);
  };

  const handleToggleCandidate = index => {
    setSelectedCandidates(prevState => ({
      ...prevState,
      [index]: prevState[index] === false,
    }));
  };

  const handleCreateTasks = async () => {
    if (!selectedTaskCandidates.length) {
      Alert.alert('未选择任务', '请至少选择一个提取的任务。');
      return;
    }

    setSubmittingTasks(true);
    const createdCount = await onCreateTasks(
      selectedTaskCandidates,
      result?.trace?.project_theme || result?.trace?.source_summary || '',
    );
    setSubmittingTasks(false);

    if (createdCount > 0) {
      Alert.alert('任务已创建', `已从图片中成功添加 ${createdCount} 个任务。`);
      onClose();
      return;
    }

    Alert.alert('创建失败', '所选任务候选项未能成功创建，请重试。');
  };

  return (
    <Modal
      transparent
      animationType="slide"
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>图片提取任务</Text>
              <Text style={styles.subtitle}>
                将截图、白板、手写笔记转换为结构化任务。
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            <TouchableOpacity style={styles.imagePicker} onPress={handlePickImage}>
              {imageAsset?.uri ? (
                <Image source={{ uri: imageAsset.uri }} style={styles.previewImage} />
              ) : (
                <View style={styles.imagePlaceholder}>
                  <Text style={styles.imagePlaceholderTitle}>点击选择图片</Text>
                  <Text style={styles.imagePlaceholderText}>
                    支持截图、白板照片、手写笔记等图片。
                  </Text>
                </View>
              )}
            </TouchableOpacity>

            <Text style={styles.label}>备注</Text>
            <TextInput
              style={styles.notesInput}
              placeholder="可选：补充图片背景说明，例如来源或重点关注方向..."
              value={notes}
              onChangeText={setNotes}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />

            <View style={styles.settingRow}>
              <Text style={styles.label}>最多提取任务数</Text>
              <View style={styles.stepper}>
                <TouchableOpacity
                  style={styles.stepperButton}
                  onPress={() => setMaxTasks(current => Math.max(1, current - 1))}
                >
                  <Text style={styles.stepperButtonText}>-</Text>
                </TouchableOpacity>
                <Text style={styles.stepperValue}>{maxTasks}</Text>
                <TouchableOpacity
                  style={styles.stepperButton}
                  onPress={() => setMaxTasks(current => Math.min(10, current + 1))}
                >
                  <Text style={styles.stepperButtonText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.primaryButton, loading && styles.primaryButtonDisabled]}
              onPress={handleAnalyze}
              disabled={loading}
            >
              {loading ? (
                <View style={styles.buttonContent}>
                  <ActivityIndicator color="#fff" />
                  <Text style={styles.primaryButtonText}>正在分析图片...</Text>
                </View>
              ) : (
                <Text style={styles.primaryButtonText}>分析图片</Text>
              )}
            </TouchableOpacity>

            {result ? (
              <View style={styles.resultCard}>
                <Text style={styles.resultTitle}>提取结果</Text>
                <Text style={styles.resultSummary}>{result.scene_summary}</Text>
                {result.trace?.project_theme ? (
                  <Text style={styles.contextText}>
                    背景：{result.trace.project_theme}
                  </Text>
                ) : null}

                {result.trace?.events?.length ? (
                  <View style={styles.traceBadge}>
                    <Text style={styles.traceBadgeText}>
                      {result.trace.events.length} 条追踪事件已记录
                    </Text>
                  </View>
                ) : null}

                {(result.task_candidates || []).map((candidate, index) => {
                  const selected = selectedCandidates[index] !== false;
                  return (
                    <TouchableOpacity
                      key={`${candidate.name}-${index}`}
                      style={[styles.candidateCard, selected && styles.candidateCardSelected]}
                      onPress={() => handleToggleCandidate(index)}
                    >
                      <View style={styles.candidateHeader}>
                        <View style={styles.checkbox}>
                          {selected ? <View style={styles.checkboxInner} /> : null}
                        </View>
                        <View style={styles.candidateContent}>
                          <Text style={styles.candidateName}>{candidate.name}</Text>
                          <Text style={styles.candidateDescription}>{candidate.description}</Text>
                        </View>
                        <View style={styles.confidencePill}>
                          <Text style={styles.confidenceText}>
                            {Math.round((candidate.confidence || 0) * 100)}%
                          </Text>
                        </View>
                      </View>
                      <View style={styles.metaRow}>
                        <Text style={styles.metaText}>优先级：{candidate.priority}</Text>
                        <Text style={styles.metaText}>
                          预计：{candidate.estimated_hours}h
                        </Text>
                      </View>
                      {candidate.source_snippet ? (
                        <Text style={styles.snippetText}>
                          来源：{candidate.source_snippet}
                        </Text>
                      ) : null}
                    </TouchableOpacity>
                  );
                })}

                {(result.trace?.warnings || result.warnings || []).length ? (
                  <View style={styles.warningBox}>
                    {(result.warnings || []).map((warning, index) => (
                      <Text key={`${warning}-${index}`} style={styles.warningText}>
                        {warning}
                      </Text>
                    ))}
                  </View>
                ) : null}

                <TouchableOpacity
                  style={[
                    styles.secondaryButton,
                    (!selectedTaskCandidates.length || submittingTasks) && styles.secondaryButtonDisabled,
                  ]}
                  onPress={handleCreateTasks}
                  disabled={!selectedTaskCandidates.length || submittingTasks}
                >
                  {submittingTasks ? (
                    <View style={styles.buttonContent}>
                      <ActivityIndicator color={COLORS.primary} />
                      <Text style={styles.secondaryButtonText}>正在创建任务...</Text>
                    </View>
                  ) : (
                    <Text style={styles.secondaryButtonText}>
                      创建 {selectedTaskCandidates.length} 个已选任务
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : null}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};


const styles = {
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 28,
    maxHeight: '92%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.text1,
  },
  subtitle: {
    marginTop: 4,
    fontSize: 14,
    color: COLORS.text2,
    lineHeight: 20,
    maxWidth: 260,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.surface2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text2,
  },
  imagePicker: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderStyle: 'dashed',
    borderRadius: 18,
    backgroundColor: COLORS.surface2,
    overflow: 'hidden',
    marginBottom: 18,
  },
  previewImage: {
    width: '100%',
    height: 180,
  },
  imagePlaceholder: {
    paddingVertical: 36,
    paddingHorizontal: 18,
    alignItems: 'center',
  },
  imagePlaceholderTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text1,
    marginBottom: 6,
  },
  imagePlaceholderText: {
    fontSize: 13,
    color: COLORS.text2,
    textAlign: 'center',
    lineHeight: 18,
  },
  label: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.text2,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 8,
  },
  notesInput: {
    minHeight: 96,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface2,
    padding: 14,
    fontSize: 15,
    color: COLORS.text1,
    marginBottom: 18,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface2,
    borderRadius: 999,
    padding: 4,
  },
  stepperButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  stepperValue: {
    width: 36,
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text1,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
    marginBottom: 20,
  },
  primaryButtonDisabled: {
    opacity: 0.7,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  resultCard: {
    backgroundColor: COLORS.surface2,
    borderRadius: 20,
    padding: 16,
  },
  resultTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: COLORS.text1,
    marginBottom: 6,
  },
  resultSummary: {
    fontSize: 14,
    color: COLORS.text2,
    lineHeight: 20,
  },
  contextText: {
    marginTop: 8,
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '700',
  },
  traceBadge: {
    alignSelf: 'flex-start',
    marginTop: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#E0E7FF',
  },
  traceBadgeText: {
    color: COLORS.primary,
    fontSize: 12,
    fontWeight: '700',
  },
  candidateCard: {
    marginTop: 14,
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    padding: 14,
  },
  candidateCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: '#F7F8FF',
  },
  candidateHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    marginRight: 10,
    marginTop: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.primary,
  },
  candidateContent: {
    flex: 1,
  },
  candidateName: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.text1,
  },
  candidateDescription: {
    marginTop: 4,
    fontSize: 13,
    color: COLORS.text2,
    lineHeight: 18,
  },
  confidencePill: {
    marginLeft: 10,
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 999,
  },
  confidenceText: {
    color: COLORS.success,
    fontSize: 12,
    fontWeight: '800',
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  metaText: {
    fontSize: 12,
    color: COLORS.text3,
    fontWeight: '600',
  },
  snippetText: {
    marginTop: 10,
    fontSize: 12,
    color: COLORS.text2,
    lineHeight: 17,
  },
  warningBox: {
    marginTop: 14,
    backgroundColor: '#FFF7ED',
    borderRadius: 14,
    padding: 12,
  },
  warningText: {
    color: COLORS.warning,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: '600',
  },
  secondaryButton: {
    marginTop: 16,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    paddingVertical: 15,
    alignItems: 'center',
    backgroundColor: COLORS.surface,
  },
  secondaryButtonDisabled: {
    opacity: 0.6,
  },
  secondaryButtonText: {
    color: COLORS.primary,
    fontSize: 15,
    fontWeight: '800',
  },
};


export default AIImagePlanningModal;
