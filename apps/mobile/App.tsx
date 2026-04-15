import React, { useEffect, useState } from 'react';
import { Alert, View } from 'react-native';

import AIImagePlanningModal from './src/components/AIImagePlanningModal';
import AIPlanningModal from './src/components/AIPlanningModal';
import BottomNavigation from './src/components/BottomNavigation';
import CalendarTab from './src/components/CalendarTab';
import PullDownSearch from './src/components/PullDownSearch';
import StatsTab from './src/components/StatsTab';
import TaskListTab from './src/components/TaskListTab';
import { TaskProvider } from './src/context/TaskContext';
import { useTaskOperations } from './src/hooks/useTaskOperations';
import { usePullDownSearch } from './src/hooks/usePullDownSearch';
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
      'Task Details',
      `Name: ${task.name}\n${task.description || 'No description.'}`,
      [{ text: 'Close', style: 'default' }],
    );
  };

  const handleAIPlan = (prompt, maxTasks = 5) => {
    aiPlanTasks(prompt, maxTasks);
  };

  return (
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

        <AIPlanningModal
          visible={aiModalVisible}
          onClose={() => setAiModalVisible(false)}
          onPlan={handleAIPlan}
          loading={loading}
          aiJobId={aiJobId}
        />

        <AIImagePlanningModal
          visible={aiImageModalVisible}
          onClose={() => setAiImageModalVisible(false)}
          onAnalyzeImage={aiPlanImageTasks}
          onCreateTasks={createTasksFromCandidates}
          loading={imagePlanningLoading}
        />

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
          ) : (
            <StatsTab />
          )}
        </View>

        <BottomNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      </View>
    </TaskProvider>
  );
};


export default App;
