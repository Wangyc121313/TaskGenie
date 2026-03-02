import { StyleSheet, Platform } from 'react-native';

// ─── 全局颜色令牌 ───────────────────────────────────────────
export const Colors = {
  primary:       '#6366F1',  // indigo-500
  primaryDark:   '#4F46E5',  // indigo-600
  primaryLight:  '#EEF2FF',  // indigo-50
  secondary:     '#EC4899',  // pink-500
  accent:        '#10B981',  // emerald-500
  warning:       '#F59E0B',  // amber-500
  danger:        '#EF4444',  // red-500

  bg:            '#F1F5F9',  // slate-100
  surface:       '#FFFFFF',
  surface2:      '#F8FAFF',

  text1:         '#0F172A',  // slate-900
  text2:         '#475569',  // slate-600
  text3:         '#94A3B8',  // slate-400
  border:        '#E2E8F0',  // slate-200

  highPriority:  '#EF4444',
  medPriority:   '#F59E0B',
  lowPriority:   '#10B981',
};

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg,
  },

  // 状态栏占位
  statusBarSpacer: {
    height: Platform.OS === 'ios' ? 44 : 24,
    backgroundColor: Colors.primary,
  },

  // 主内容区域
  mainContent: {
    flex: 1,
  },
});