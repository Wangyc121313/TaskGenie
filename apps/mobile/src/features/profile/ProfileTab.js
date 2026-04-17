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
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Preferences</Text>
        {loading ? <ActivityIndicator color={COLORS.primary} /> : null}
        <TextInput
          style={styles.input}
          placeholder="Display name"
          value={draftPreferences.display_name || ''}
          onChangeText={value => handlePreferenceChange('display_name', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="Work start time"
          value={draftPreferences.work_start_time || '09:00'}
          onChangeText={value => handlePreferenceChange('work_start_time', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="Work end time"
          value={draftPreferences.work_end_time || '18:00'}
          onChangeText={value => handlePreferenceChange('work_end_time', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="Planning style"
          value={draftPreferences.planning_style || 'balanced'}
          onChangeText={value => handlePreferenceChange('planning_style', value)}
        />
        <TextInput
          style={styles.input}
          placeholder="Preferred task duration hours"
          value={`${draftPreferences.preferred_task_duration_hours || 2}`}
          onChangeText={value => handlePreferenceChange('preferred_task_duration_hours', Number(value) || 2)}
          keyboardType="numeric"
        />
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => onUpdatePreferences(draftPreferences)}
        >
          <Text style={styles.primaryButtonText}>Save Preferences</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Memory Manager</Text>
        <TextInput
          style={styles.input}
          placeholder="Memory category"
          value={memoryCategory}
          onChangeText={setMemoryCategory}
        />
        <TextInput
          style={styles.input}
          placeholder="Add a confirmed memory"
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
          <Text style={styles.primaryButtonText}>Create Memory</Text>
        </TouchableOpacity>

        {memories.map(memory => (
          <View key={memory.id} style={styles.memoryCard}>
            <View style={styles.memoryHeader}>
              <View>
                <Text style={styles.memoryCategory}>{memory.category}</Text>
                <Text style={styles.memorySource}>{memory.source}</Text>
              </View>
              <TouchableOpacity onPress={() => onDeleteMemory(memory.id)}>
                <Text style={styles.deleteText}>Delete</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.memoryContent}>{memory.content}</Text>
            <View style={styles.memoryActions}>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => onUpdateMemory(memory.id, { is_active: !memory.is_active })}
              >
                <Text style={styles.secondaryButtonText}>
                  {memory.is_active ? 'Mark Inactive' : 'Reactivate'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => onUpdateMemory(memory.id, { source: 'user_edited' })}
              >
                <Text style={styles.secondaryButtonText}>Mark Reviewed</Text>
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
