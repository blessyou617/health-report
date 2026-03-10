import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import QuestionnaireScreen from '../screens/QuestionnaireScreen';
import ReportScreen from '../screens/ReportScreen';
import ChatScreen from '../screens/ChatScreen';
import { RootTabParamList } from '../types/navigation';

const Tab = createBottomTabNavigator<RootTabParamList>();

export default function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'Questionnaire') {
            iconName = focused ? 'document-text' : 'document-text-outline';
          } else if (route.name === 'Report') {
            iconName = focused ? 'analytics' : 'analytics-outline';
          } else if (route.name === 'Chat') {
            iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
          } else {
            iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
        headerShown: true,
      })}
    >
      <Tab.Screen name="Questionnaire" component={QuestionnaireScreen} options={{ title: '问卷' }} />
      <Tab.Screen name="Report" component={ReportScreen} options={{ title: '报告' }} />
      <Tab.Screen name="Chat" component={ChatScreen} options={{ title: 'AI 助手' }} />
    </Tab.Navigator>
  );
}
