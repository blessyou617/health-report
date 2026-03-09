import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

export default function ReportScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.date}>2026年3月9日</Text>
        <Text style={styles.title}>健康报告</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📊 健康评分</Text>
        <View style={styles.scoreContainer}>
          <Text style={styles.score}>85</Text>
          <Text style={styles.scoreLabel}>/ 100</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💪 健康指标</Text>
        <View style={styles.card}>
          <View style={styles指标Row}>
            <Text style={styles.指标Name}>睡眠质量</Text>
            <Text style={styles.指标Value}>良好</Text>
          </View>
          <View style={styles.指标Row}>
            <Text style={styles.指标Name}>运动频率</Text>
            <Text style={styles.指标Value}>中等</Text>
          </View>
          <View style={styles.指标Row}>
            <Text style={styles.指标Name}>压力水平</Text>
            <Text style={styles.指标Value}>较低</Text>
          </View>
          <View style={styles.指标Row}>
            <Text style={styles.指标Name}>饮水习惯</Text>
            <Text style={styles.指标Value}>需改善</Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🏥 异常指标</Text>
        <View style={styles.card}>
          <Text style={styles.normalText}>暂无异常指标</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💡 建议</Text>
        <View style={styles.card}>
          <Text style={styles.adviceText}>
            1. 建议每天保证 7-8 小时睡眠{"\n"}
            2. 增加运动频率，每周至少 3 次{"\n"}
            3. 多喝水，每天至少 6 杯{"\n"}
            4. 保持良好的作息习惯
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    alignItems: 'center',
  },
  date: {
    color: '#fff',
    fontSize: 14,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 5,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'center',
  },
  score: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  scoreLabel: {
    fontSize: 24,
    color: '#999',
    marginLeft: 5,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
  },
  指标Row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  指标Name: {
    fontSize: 16,
    color: '#333',
  },
  指标Value: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '500',
  },
  normalText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    padding: 10,
  },
  adviceText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 24,
  },
});
