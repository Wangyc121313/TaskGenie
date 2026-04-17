import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';


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


const todayString = () => new Date().toISOString().slice(0, 10);


const AssistantTab = ({ currentRun, loading, onRunAgent, onConfirmRun }) => {
  const [textPrompt, setTextPrompt] = useState('');
  const [textMaxTasks, setTextMaxTasks] = useState('5');
  const [scheduleDate, setScheduleDate] = useState(todayString());
  const [imageAsset, setImageAsset] = useState(null);
  const [imageNotes, setImageNotes] = useState('');

  const timeline = useMemo(
    () => currentRun?.trace_summary?.timeline || [],
    [currentRun],
  );

  const handleTextRun = async () => {
    await onRunAgent({
      mode: 'text_goal',
      prompt: textPrompt,
      max_tasks: Number(textMaxTasks) || 5,
      auto_execute: false,
    });
  };

  const handleScheduleRun = async () => {
    await onRunAgent({
      mode: 'schedule_day',
      date: scheduleDate,
      auto_execute: true,
    });
  };

  const handlePickImage = async () => {
    const result = await launchImageLibrary({
      mediaType: 'photo',
      selectionLimit: 1,
      includeBase64: true,
      quality: 0.8,
    });
    const asset = result.assets?.[0];
    if (!asset?.base64 || !asset?.type) {
      return;
    }
    setImageAsset(asset);
  };

  const handleImageRun = async () => {
    if (!imageAsset?.base64) {
      return;
    }
    await onRunAgent({
      mode: 'image_goal',
      image_base64: imageAsset.base64,
      image_mime_type: imageAsset.type,
      filename: imageAsset.fileName || 'selected-image',
      notes: imageNotes,
      max_tasks: 5,
      auto_execute: false,
    });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>AI Assistant</Text>
        <Text style={styles.title}>Plan, inspect, confirm, and learn from every run.</Text>
        <Text style={styles.subtitle}>
          The assistant exposes the actual agent flow instead of hiding it behind a single button.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Text Goal to Tasks</Text>
        <TextInput
          style={styles.input}
          placeholder="Describe the goal you want the agent to break down."
          value={textPrompt}
          onChangeText={setTextPrompt}
          multiline
        />
        <TextInput
          style={styles.input}
          placeholder="Max tasks"
          value={textMaxTasks}
          onChangeText={setTextMaxTasks}
          keyboardType="numeric"
        />
        <TouchableOpacity style={styles.primaryButton} onPress={handleTextRun} disabled={loading}>
          <Text style={styles.primaryButtonText}>Run Text Agent</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Image to Tasks</Text>
        <TouchableOpacity style={styles.imagePicker} onPress={handlePickImage}>
          {imageAsset?.uri ? (
            <Image source={{ uri: imageAsset.uri }} style={styles.imagePreview} />
          ) : (
            <Text style={styles.imagePlaceholder}>Select an image to extract candidate tasks.</Text>
          )}
        </TouchableOpacity>
        <TextInput
          style={styles.input}
          placeholder="Optional notes for the image context"
          value={imageNotes}
          onChangeText={setImageNotes}
          multiline
        />
        <TouchableOpacity style={styles.primaryButton} onPress={handleImageRun} disabled={loading}>
          <Text style={styles.primaryButtonText}>Run Image Agent</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Schedule Existing Tasks</Text>
        <TextInput
          style={styles.input}
          placeholder="YYYY-MM-DD"
          value={scheduleDate}
          onChangeText={setScheduleDate}
        />
        <TouchableOpacity style={styles.primaryButton} onPress={handleScheduleRun} disabled={loading}>
          <Text style={styles.primaryButtonText}>Generate Day Schedule</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <View style={styles.resultHeader}>
          <View>
            <Text style={styles.cardTitle}>Agent Run</Text>
            <Text style={styles.cardMeta}>
              Strategy: {currentRun?.strategy || 'plan_execute'}
            </Text>
          </View>
          {loading ? <ActivityIndicator color={COLORS.primary} /> : null}
        </View>

        {currentRun ? (
          <>
            <View style={styles.summaryRow}>
              <SummaryPill label="Stage" value={currentRun.trace_summary.current_stage} />
              <SummaryPill label="Memory" value={`${currentRun.trace_summary.used_memory_count}`} />
              <SummaryPill label="Tools" value={`${currentRun.trace_summary.executed_tool_count}`} />
            </View>

            <Text style={styles.runTitle}>
              {currentRun.trace_summary.goal_summary || 'No goal summary available'}
            </Text>
            {currentRun.requires_confirmation ? (
              <TouchableOpacity
                style={styles.confirmButton}
                onPress={() => onConfirmRun(currentRun.job_id)}
              >
                <Text style={styles.confirmButtonText}>Confirm Side-Effecting Actions</Text>
              </TouchableOpacity>
            ) : null}

            <SectionTitle title="Timeline" />
            {timeline.length ? (
              timeline.map((item, index) => (
                <View key={`${item.timestamp}-${index}`} style={styles.timelineItem}>
                  <Text style={styles.timelineStage}>{item.stage}</Text>
                  <Text style={styles.timelineDecision}>{item.decision}</Text>
                  <Text style={styles.timelineObservation}>{item.observation}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.emptyState}>Run the agent to see timeline events.</Text>
            )}

            {!!currentRun.artifacts?.planned_tasks?.length && (
              <>
                <SectionTitle title="Planned Tasks" />
                {currentRun.artifacts.planned_tasks.map((task, index) => (
                  <View key={`${task.name}-${index}`} style={styles.listCard}>
                    <Text style={styles.listTitle}>{task.name}</Text>
                    <Text style={styles.listDescription}>{task.description}</Text>
                  </View>
                ))}
              </>
            )}

            {!!currentRun.artifacts?.task_candidates?.length && (
              <>
                <SectionTitle title="Image Candidates" />
                {currentRun.artifacts.task_candidates.map((task, index) => (
                  <View key={`${task.name}-${index}`} style={styles.listCard}>
                    <Text style={styles.listTitle}>{task.name}</Text>
                    <Text style={styles.listDescription}>{task.description}</Text>
                  </View>
                ))}
              </>
            )}

            {!!currentRun.artifacts?.created_tasks?.length && (
              <>
                <SectionTitle title="Created Tasks" />
                {currentRun.artifacts.created_tasks.map((task, index) => (
                  <View key={`${task.id || task.name}-${index}`} style={styles.listCard}>
                    <Text style={styles.listTitle}>{task.name}</Text>
                    <Text style={styles.listDescription}>{task.description}</Text>
                  </View>
                ))}
              </>
            )}

            {currentRun.artifacts?.schedule?.schedule_items?.length ? (
              <>
                <SectionTitle title="Schedule" />
                {currentRun.artifacts.schedule.schedule_items.map((item, index) => (
                  <View key={`${item.task_id}-${index}`} style={styles.listCard}>
                    <Text style={styles.listTitle}>
                      {item.start_time} - {item.end_time}
                    </Text>
                    <Text style={styles.listDescription}>{item.task_name}</Text>
                  </View>
                ))}
              </>
            ) : null}
          </>
        ) : (
          <Text style={styles.emptyState}>No agent run yet.</Text>
        )}
      </View>
    </ScrollView>
  );
};


const SummaryPill = ({ label, value }) => (
  <View style={styles.summaryPill}>
    <Text style={styles.summaryLabel}>{label}</Text>
    <Text style={styles.summaryValue}>{value}</Text>
  </View>
);


const SectionTitle = ({ title }) => (
  <Text style={styles.sectionTitle}>{title}</Text>
);


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
    marginBottom: 16,
  },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    color: COLORS.text1,
    fontSize: 24,
    fontWeight: '800',
    marginBottom: 8,
  },
  subtitle: {
    color: COLORS.text2,
    fontSize: 14,
    lineHeight: 20,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardTitle: {
    color: COLORS.text1,
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 10,
  },
  cardMeta: {
    color: COLORS.text3,
    fontSize: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: '#FFFFFF',
    padding: 12,
    color: COLORS.text1,
    marginBottom: 12,
    minHeight: 48,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  imagePicker: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface2,
    minHeight: 120,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    overflow: 'hidden',
  },
  imagePreview: {
    width: '100%',
    height: 180,
  },
  imagePlaceholder: {
    color: COLORS.text2,
    paddingHorizontal: 20,
    textAlign: 'center',
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  summaryRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  summaryPill: {
    backgroundColor: COLORS.surface2,
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginRight: 8,
  },
  summaryLabel: {
    color: COLORS.text3,
    fontSize: 11,
  },
  summaryValue: {
    color: COLORS.text1,
    fontSize: 13,
    fontWeight: '700',
  },
  runTitle: {
    color: COLORS.text1,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  confirmButton: {
    backgroundColor: COLORS.success,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  confirmButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  sectionTitle: {
    color: COLORS.text1,
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 10,
    marginTop: 4,
  },
  timelineItem: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
    paddingLeft: 12,
    marginBottom: 12,
  },
  timelineStage: {
    color: COLORS.text3,
    fontSize: 12,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  timelineDecision: {
    color: COLORS.text1,
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  timelineObservation: {
    color: COLORS.text2,
    fontSize: 13,
    lineHeight: 18,
  },
  listCard: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    padding: 12,
    marginBottom: 10,
  },
  listTitle: {
    color: COLORS.text1,
    fontWeight: '700',
    marginBottom: 4,
  },
  listDescription: {
    color: COLORS.text2,
    lineHeight: 18,
    fontSize: 13,
  },
  emptyState: {
    color: COLORS.text3,
    fontSize: 14,
  },
};


export default AssistantTab;
