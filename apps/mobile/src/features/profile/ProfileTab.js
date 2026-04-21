import React, { useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';


const COLORS = {
  bg: '#F8FAFC',
  surface: '#FFFFFF',
  surface2: '#EEF2FF',
  border: '#E2E8F0',
  primary: '#4F46E5',
  success: '#059669',
  text1: '#0F172A',
  text2: '#475569',
  text3: '#94A3B8',
  danger: '#DC2626',
};


const ProfileTab = ({
  preferences,
  memories,
  loading,
  onUpdatePreferences,
  onCreateMemory,
  onUpdateMemory,
  onDeleteMemory,
}) => {
  const [draftPreferences, setDraftPreferences] = useState(preferences);
  const [memoryContent, setMemoryContent] = useState('');
  const [memoryCategory, setMemoryCategory] = useState('context');

  React.useEffect(() => {
    setDraftPreferences(preferences);
  }, [preferences]);

  const handlePreferenceChange = (field, value) => {
    setDraftPreferences(prevState => ({
      ...prevState,
      [field]: value,
    }));
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>👤 我的</Text>
        <Text style={styles.heroSubtitle}>
          在这里设置你的工作习惯和时间偏好，AI 会根据这些信息为你生成更贴合实际的任务日程。
          记忆模块会记录 Agent 了解到的你的背景信息，方便下次更精准地规划任务。
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>个人偏好</Text>
        <Text style={styles.cardDesc}>设置工作时间和规划风格，AI 在生成日程时会遵循这些偏好。</Text>
        {loading ? <ActivityIndicator color={COLORS.primary} /> : null}
        <TextInput
          style={styles.input}
          placeholder="显示名称"
          value={draftPreferences.display_name || ''}
          onChangeText={value => handlePreferenceChange('display_name', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="工作开始时间（如 09:00）"
          value={draftPreferences.work_start_time || '09:00'}
          onChangeText={value => handlePreferenceChange('work_start_time', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="工作结束时间（如 18:00）"
          value={draftPreferences.work_end_time || '18:00'}
          onChangeText={value => handlePreferenceChange('work_end_time', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="规划风格（balanced / aggressive / relaxed）"
          value={draftPreferences.planning_style || 'balanced'}
          onChangeText={value => handlePreferenceChange('planning_style', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="单个任务默认时长（小时）"
          value={`${draftPreferences.preferred_task_duration_hours || 2}`}
          onChangeText={value => handlePreferenceChange('preferred_task_duration_hours', Number(value) || 2)}
          keyboardType="numeric"
        />
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => onUpdatePreferences(draftPreferences)}
        >
          <Text style={styles.primaryButtonText}>保存偏好</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>记忆管理</Text>
        <Text style={styles.cardDesc}>Agent 在运行过程中会自动记录一些背景知识。你也可以手动添加或删除记忆条目，让 AI 更了解你。</Text>
        <TextInput
          style={styles.input}
          placeholder="记忆类别（如 context / preference）"
          value={memoryCategory}
          onChangeText={setMemoryCategory}
        />
        <TextInput
          style={styles.input}
          placeholder="输入记忆内容"
          value={memoryContent}
          onChangeText={setMemoryContent}
          multiline
        />
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={async () => {
            if (!memoryContent.trim()) {
              return;
            }
            await onCreateMemory({
              category: memoryCategory,
              source: 'user_confirmed',
              content: memoryContent,
              tags: ['manual'],
            });
            setMemoryContent('');
          }}
        >
          <Text style={styles.primaryButtonText}>创建记忆</Text>
        </TouchableOpacity>

        {memories.map(memory => (
          <View key={memory.id} style={styles.memoryCard}>
            <View style={styles.memoryHeader}>
              <View>
                <Text style={styles.memoryCategory}>{memory.category}</Text>
                <Text style={styles.memorySource}>{memory.source}</Text>
              </View>
              <TouchableOpacity onPress={() => onDeleteMemory(memory.id)}>
                <Text style={styles.deleteText}>删除</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.memoryContent}>{memory.content}</Text>
            <View style={styles.memoryActions}>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => onUpdateMemory(memory.id, { is_active: !memory.is_active })}
              >
                <Text style={styles.secondaryButtonText}>
                  {memory.is_active ? '标记不活跃' : '重新激活'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => onUpdateMemory(memory.id, { source: 'user_edited' })}
              >
                <Text style={styles.secondaryButtonText}>标记已审阅</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};


const styles = {
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  hero: {
    paddingHorizontal: 4,
    paddingTop: 8,
    paddingBottom: 16,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.text1,
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 13,
    color: COLORS.text2,
    lineHeight: 20,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    color: COLORS.text1,
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 4,
  },
  cardDesc: {
    color: COLORS.text2,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    padding: 12,
    color: COLORS.text1,
    marginBottom: 12,
    backgroundColor: '#FFFFFF',
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 6,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  memoryCard: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    padding: 12,
    marginTop: 12,
  },
  memoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  memoryCategory: {
    color: COLORS.primary,
    fontWeight: '800',
    textTransform: 'uppercase',
    fontSize: 12,
  },
  memorySource: {
    color: COLORS.text3,
    fontSize: 11,
  },
  memoryContent: {
    color: COLORS.text1,
    lineHeight: 18,
  },
  memoryActions: {
    flexDirection: 'row',
    marginTop: 12,
  },
  secondaryButton: {
    backgroundColor: COLORS.surface2,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  secondaryButtonText: {
    color: COLORS.primary,
    fontWeight: '700',
    fontSize: 12,
  },
  deleteText: {
    color: COLORS.danger,
    fontWeight: '700',
  },
};


export default ProfileTab;
