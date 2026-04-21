import React, { useEffect, useState } from 'react';
import { Alert, View } from 'react-native';

import AIImagePlanningModal from './src/components/AIImagePlanningModal';
import AIPlanningModal from './src/components/AIPlanningModal';
import AppErrorBoundary from './src/components/AppErrorBoundary';
import BottomNavigation from './src/components/BottomNavigation';
import CalendarTab from './src/components/CalendarTab';
import PullDownSearch from './src/components/PullDownSearch';
import TaskListTab from './src/components/TaskListTab';
import { TaskProvider } from './src/context/TaskContext';
import AssistantTab from './src/features/assistant/AssistantTab';
import ProfileTab from './src/features/profile/ProfileTab';
import { useAgentAssistant } from './src/hooks/useAgentAssistant';
import { useProfileData } from './src/hooks/useProfileData';
import { usePullDownSearch } from './src/hooks/usePullDownSearch';
import { useTaskOperations } from './src/hooks/useTaskOperations';
import { styles } from './src/styles/AppStyles';


const App = () => {
  const [activeTab, setActiveTab] = useState('tasks');
  const [aiModalVisible, setAiModalVisible] = useState(false);
  const [aiImageModalVisible, setAiImageModalVisible] = useState(false);

  const {
    tasks,
    loading,
    imagePlanningLoading,
    aiJobId,
    fetchTasks,
    createTask,
    createTasksFromCandidates,
    updateTask,
    toggleTaskCompletion,
    deleteTask,
    aiPlanTasks,
    aiPlanImageTasks,
  } = useTaskOperations();

  const {
    currentRun,
    loading: agentLoading,
    runAgent,
    confirmRun,
  } = useAgentAssistant({ onTasksChanged: fetchTasks });

  const {
    preferences,
    memories,
    loading: profileLoading,
    updatePreferences,
    createMemory,
    updateMemory,
    deleteMemory,
  } = useProfileData();

  const {
    searchVisible,
    searchTranslateY,
    searchOpacity,
    pullDownPanResponder,
    pullUpPanResponder,
    closeSearch,
  } = usePullDownSearch();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleTaskSelect = task => {
    Alert.alert(
      '任务详情',
      `名称：${task.name}\n${task.description || '暂无描述'}`,
      [{ text: '关闭', style: 'default' }],
    );
  };

  const handleAIPlan = (prompt, maxTasks = 5) => {
    aiPlanTasks(prompt, maxTasks);
  };

  return (
    <AppErrorBoundary>
      <TaskProvider>
        <View style={styles.container}>
          <View style={styles.statusBarSpacer} />

          <PullDownSearch
            visible={searchVisible}
            onClose={closeSearch}
            tasks={tasks}
            onTaskSelect={handleTaskSelect}
            translateY={searchTranslateY}
            opacity={searchOpacity}
          />

          {aiModalVisible ? (
            <AIPlanningModal
              visible={aiModalVisible}
              onClose={() => setAiModalVisible(false)}
              onPlan={handleAIPlan}
              loading={loading}
              aiJobId={aiJobId}
            />
          ) : null}

          {aiImageModalVisible ? (
            <AIImagePlanningModal
              visible={aiImageModalVisible}
              onClose={() => setAiImageModalVisible(false)}
              onAnalyzeImage={aiPlanImageTasks}
              onCreateTasks={createTasksFromCandidates}
              loading={imagePlanningLoading}
            />
          ) : null}

          <View style={styles.mainContent} {...pullDownPanResponder.panHandlers}>
            {activeTab === 'tasks' ? (
              <TaskListTab
                tasks={tasks}
                onCreateTask={createTask}
                onUpdateTask={updateTask}
                onDeleteTask={deleteTask}
                onToggleTaskCompletion={toggleTaskCompletion}
                onOpenAIModal={() => setAiModalVisible(true)}
                onOpenAIImageModal={() => setAiImageModalVisible(true)}
                pullUpPanResponder={pullUpPanResponder}
              />
            ) : activeTab === 'calendar' ? (
              <CalendarTab pullUpPanResponder={pullUpPanResponder} />
            ) : activeTab === 'assistant' ? (
              <AssistantTab
                currentRun={currentRun}
                loading={agentLoading}
                onRunAgent={runAgent}
                onConfirmRun={confirmRun}
              />
            ) : (
              <ProfileTab
                preferences={preferences}
                memories={memories}
                loading={profileLoading}
                onUpdatePreferences={updatePreferences}
                onCreateMemory={createMemory}
                onUpdateMemory={updateMemory}
                onDeleteMemory={deleteMemory}
              />
            )}
          </View>

          <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
        </View>
      </TaskProvider>
    </AppErrorBoundary>
  );
};


export default App;
