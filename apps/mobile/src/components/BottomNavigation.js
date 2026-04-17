import React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';

import { styles } from '../styles/ComponentStyles';


const BottomNavigation = ({ activeTab, onTabChange }) => {
  return (
    <View style={styles.bottomNavigation}>
      <TouchableOpacity
        style={[styles.bottomNavButton, activeTab === 'tasks' && styles.activeBottomNavButton]}
        onPress={() => onTabChange('tasks')}
      >
        <Text style={[styles.bottomNavIcon, activeTab === 'tasks' && styles.activeBottomNavIcon]}>
          TL
        </Text>
        <Text style={[styles.bottomNavText, activeTab === 'tasks' && styles.activeBottomNavText]}>
          Tasks
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.bottomNavButton, activeTab === 'calendar' && styles.activeBottomNavButton]}
        onPress={() => onTabChange('calendar')}
      >
        <Text
          style={[
            styles.bottomNavIcon,
            activeTab === 'calendar' && styles.activeBottomNavIcon,
          ]}
        >
          CA
        </Text>
        <Text style={[styles.bottomNavText, activeTab === 'calendar' && styles.activeBottomNavText]}>
          Calendar
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.bottomNavButton, activeTab === 'assistant' && styles.activeBottomNavButton]}
        onPress={() => onTabChange('assistant')}
      >
        <Text
          style={[
            styles.bottomNavIcon,
            activeTab === 'assistant' && styles.activeBottomNavIcon,
          ]}
        >
          AI
        </Text>
        <Text style={[styles.bottomNavText, activeTab === 'assistant' && styles.activeBottomNavText]}>
          Assistant
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.bottomNavButton, activeTab === 'profile' && styles.activeBottomNavButton]}
        onPress={() => onTabChange('profile')}
      >
        <Text
          style={[
            styles.bottomNavIcon,
            activeTab === 'profile' && styles.activeBottomNavIcon,
          ]}
        >
          ME
        </Text>
        <Text style={[styles.bottomNavText, activeTab === 'profile' && styles.activeBottomNavText]}>
          Profile
        </Text>
      </TouchableOpacity>
    </View>
  );
};


export default BottomNavigation;
