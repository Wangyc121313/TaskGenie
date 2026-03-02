import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { API_URL } from '../context/TaskContext';

const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 48) / 2;

const StatsTab = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/stats`);
      const data = await response.json();
      setStats(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('获取统计失败:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
        <Text style={styles.loadingText}>加载统计数据...</Text>
      </View>
    );
  }

  if (!stats) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.errorText}>暂无数据，请检查后端连接</Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchStats}>
          <Text style={styles.retryText}>重试</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const completionRate = stats.total > 0
    ? Math.round((stats.completed / stats.total) * 100)
    : 0;

  const maxPriorityCount = Math.max(
    stats.by_priority?.high || 0,
    stats.by_priority?.medium || 0,
    stats.by_priority?.low || 0,
    1,
  );

  const formattedTime = lastUpdated
    ? `${lastUpdated.getHours().toString().padStart(2, '0')}:${lastUpdated.getMinutes().toString().padStart(2, '0')}`
    : '--:--';

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366F1" />}
      showsVerticalScrollIndicator={false}
    >
      {/* 顶部标题栏 */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>📊 数据统计</Text>
          <Text style={styles.headerSubtitle}>上次更新 {formattedTime}</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchStats}>
          <Text style={styles.refreshBtnText}>刷新</Text>
        </TouchableOpacity>
      </View>

      {/* 概览卡片 2×2 */}
      <View style={styles.cardsGrid}>
        <StatCard label="全部任务" value={stats.total} icon="🗂" color="#6366F1" />
        <StatCard label="已完成" value={stats.completed} icon="✅" color="#2ecc71" />
        <StatCard label="待完成" value={stats.pending} icon="⏳" color="#f39c12" />
        <StatCard label="已逾期" value={stats.overdue} icon="⚠️" color="#e74c3c" />
      </View>

      {/* 完成率 */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>完成率</Text>
          <Text style={[styles.rateText, { color: completionRate >= 70 ? '#2ecc71' : completionRate >= 40 ? '#f39c12' : '#e74c3c' }]}>
            {completionRate}%
          </Text>
        </View>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${completionRate}%`, backgroundColor: completionRate >= 70 ? '#2ecc71' : completionRate >= 40 ? '#f39c12' : '#e74c3c' }]} />
        </View>
        <View style={styles.progressLabels}>
          <Text style={styles.progressLabel}>0%</Text>
          <Text style={styles.progressLabel}>{stats.completed} / {stats.total} 个任务</Text>
          <Text style={styles.progressLabel}>100%</Text>
        </View>
      </View>

      {/* 按优先级 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>按优先级分布</Text>
        <PriorityBar label="🔴 高优先级" count={stats.by_priority?.high || 0} max={maxPriorityCount} color="#e74c3c" />
        <PriorityBar label="🟡 中优先级" count={stats.by_priority?.medium || 0} max={maxPriorityCount} color="#f39c12" />
        <PriorityBar label="🟢 低优先级" count={stats.by_priority?.low || 0} max={maxPriorityCount} color="#2ecc71" />
      </View>

      {/* 按标签 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>标签分布</Text>
        <View style={styles.tagsGrid}>
          {Object.entries(stats.by_tags || {}).map(([tag, count]) => (
            <TagBadge key={tag} tag={tag} count={count} />
          ))}
        </View>
      </View>

      {/* 今日概览 */}
      <View style={[styles.section, styles.todaySection]}>
        <Text style={styles.sectionTitle}>今日概览</Text>
        <View style={styles.todayRow}>
          <View style={styles.todayItem}>
            <Text style={styles.todayValue}>{stats.due_today}</Text>
            <Text style={styles.todayLabel}>今日到期</Text>
          </View>
          <View style={styles.todayDivider} />
          <View style={styles.todayItem}>
            <Text style={[styles.todayValue, { color: '#e74c3c' }]}>{stats.overdue}</Text>
            <Text style={styles.todayLabel}>需立即处理</Text>
          </View>
          <View style={styles.todayDivider} />
          <View style={styles.todayItem}>
            <Text style={[styles.todayValue, { color: '#2ecc71' }]}>{stats.completed}</Text>
            <Text style={styles.todayLabel}>累计完成</Text>
          </View>
        </View>
      </View>

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
};

// 概览卡片子组件
const StatCard = ({ label, value, icon, color }) => (
  <View style={[styles.card, { borderLeftColor: color }]}>
    <Text style={styles.cardIcon}>{icon}</Text>
    <Text style={[styles.cardValue, { color }]}>{value}</Text>
    <Text style={styles.cardLabel}>{label}</Text>
  </View>
);

// 优先级条形图子组件
const PriorityBar = ({ label, count, max, color }) => {
  const barWidth = max > 0 ? (count / max) * 100 : 0;
  return (
    <View style={styles.barRow}>
      <Text style={styles.barLabel}>{label}</Text>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${barWidth}%`, backgroundColor: color }]} />
      </View>
      <Text style={[styles.barCount, { color }]}>{count}</Text>
    </View>
  );
};

// 标签徽章子组件
const TAG_COLORS = {
  '今日': '#6366F1',
  '明日': '#2ecc71',
  '重要': '#e74c3c',
  '已完成': '#95a5a6',
  '已过期': '#e67e22',
};

const TagBadge = ({ tag, count }) => (
  <View style={[styles.tagBadge, { backgroundColor: TAG_COLORS[tag] || '#bdc3c7' }]}>
    <Text style={styles.tagBadgeText}>{tag}</Text>
    <View style={styles.tagBadgeCount}>
      <Text style={styles.tagBadgeCountText}>{count}</Text>
    </View>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F1F5F9',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
  },
  loadingText: {
    marginTop: 12,
    color: '#94A3B8',
    fontSize: 14,
  },
  errorText: {
    color: '#EF4444',
    fontSize: 15,
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 20,
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
  },

  // 顶部标题
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#6366F1',
    paddingHorizontal: 20,
    paddingVertical: 18,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.65)',
    marginTop: 3,
  },
  refreshBtn: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 14,
  },
  refreshBtnText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },

  // 卡片网格
  cardsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 14,
    gap: 12,
  },
  card: {
    width: CARD_WIDTH,
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 16,
    borderLeftWidth: 4,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
    alignItems: 'flex-start',
  },
  cardIcon: {
    fontSize: 26,
    marginBottom: 10,
  },
  cardValue: {
    fontSize: 34,
    fontWeight: '800',
    lineHeight: 38,
  },
  cardLabel: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
    fontWeight: '500',
  },

  // 通用分区
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 14,
    marginBottom: 12,
    borderRadius: 18,
    padding: 18,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 14,
  },

  // 完成率
  rateText: {
    fontSize: 26,
    fontWeight: '800',
  },
  progressTrack: {
    height: 10,
    backgroundColor: '#F1F5F9',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 5,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  progressLabel: {
    fontSize: 11,
    color: '#94A3B8',
  },

  // 优先级条形图
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  barLabel: {
    width: 90,
    fontSize: 13,
    color: '#475569',
  },
  barTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 4,
    overflow: 'hidden',
    marginHorizontal: 8,
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
    minWidth: 4,
  },
  barCount: {
    width: 24,
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'right',
  },

  // 标签网格
  tagsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tagBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  tagBadgeText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
    marginRight: 6,
  },
  tagBadgeCount: {
    backgroundColor: 'rgba(255,255,255,0.28)',
    borderRadius: 8,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  tagBadgeCountText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },

  // 今日概览
  todaySection: {
    marginBottom: 0,
  },
  todayRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 6,
  },
  todayItem: {
    alignItems: 'center',
    flex: 1,
  },
  todayValue: {
    fontSize: 30,
    fontWeight: '800',
    color: '#6366F1',
  },
  todayLabel: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
  },
  todayDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E2E8F0',
  },

  bottomSpacer: {
    height: 24,
  },
});

export default StatsTab;

