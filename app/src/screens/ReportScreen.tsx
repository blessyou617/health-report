import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Share } from 'react-native';
import { generateVoiceReport, generateTextReport } from '../services/reportShare';

const sampleReport = {
  date: '2026年3月9日',
  score: 85,
  indicators: [
    { name: '睡眠质量', value: '良好' },
    { name: '运动频率', value: '中等' },
    { name: '压力水平', value: '较低' },
    { name: '饮水习惯', value: '需改善' },
  ],
  advice: '1. 建议每天保证 7-8 小时睡眠\n2. 增加运动频率，每周至少 3 次\n3. 多喝水，每天至少 6 杯\n4. 保持良好的作息习惯',
};

export default function ReportScreen() {
  const { date, score, indicators, advice } = sampleReport;

  const handleShareText = async () => {
    try {
      const text = generateTextReport(sampleReport);
      await Share.share({
        message: text,
        title: '健康报告',
      });
    } catch (error) {
      Alert.alert('分享失败', '请重试');
    }
  };

  const handleShareVoice = () => {
    const text = generateVoiceReport(sampleReport);
    Alert.alert('语音报告', '已生成语音，点击确定后开始播放', [
      { text: '取消', style: 'cancel' },
      { text: '播放', onPress: () => generateVoiceReport(sampleReport) },
    ]);
  };

  const handleWechatShare = () => {
    // TODO: 集成微信分享
    Alert.alert(
      '微信分享',
      '请先在设置中绑定微信账号',
      [{ text: '确定' }]
    );
  };

  const handlePayment = () => {
    // TODO: 集成微信支付
    Alert.alert(
      '解锁完整报告',
      '¥9.9 解锁 AI 详细分析和语音报告',
      [
        { text: '取消', style: 'cancel' },
        { text: '微信支付', onPress: () => handleWechatPay() },
      ]
    );
  };

  const handleWechatPay = () => {
    // TODO: 实际调用微信支付 API
    Alert.alert('提示', '微信支付功能需要配置商户信息');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.date}>{date}</Text>
        <Text style={styles.title}>健康报告</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📊 健康评分</Text>
        <View style={styles.scoreContainer}>
          <Text style={styles.score}>{score}</Text>
          <Text style={styles.scoreLabel}>/ 100</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💪 健康指标</Text>
        <View style={styles.card}>
          {indicators.map((indicator, index) => (
            <View key={index} style={styles.indicatorRow}>
              <Text style={styles.indicatorName}>{indicator.name}</Text>
              <Text style={styles.indicatorValue}>{indicator.value}</Text>
            </View>
          ))}
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
          <Text style={styles.adviceText}>{advice}</Text>
        </View>
      </View>

      {/* 分享功能 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📤 分享报告</Text>
        <View style={styles.shareButtons}>
          <TouchableOpacity style={[styles.shareButton, styles.wechatButton]} onPress={handleWechatShare}>
            <Text style={styles.shareButtonText}>💬 微信好友</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.shareButton, styles.textButton]} onPress={handleShareText}>
            <Text style={styles.shareButtonText}>📝 文字分享</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.shareButton, styles.voiceButton]} onPress={handleShareVoice}>
            <Text style={styles.shareButtonText}>🔊 语音播报</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 付费功能 */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.vipButton} onPress={handlePayment}>
          <Text style={styles.vipButtonText}>💎 解锁完整 AI 报告 (¥9.9)</Text>
        </TouchableOpacity>
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
    backgroundColor: '#07C160',
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
    color: '#07C160',
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
  indicatorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  indicatorName: {
    fontSize: 16,
    color: '#333',
  },
  indicatorValue: {
    fontSize: 16,
    color: '#07C160',
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
  shareButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  shareButton: {
    flex: 1,
    minWidth: '45%',
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
  },
  wechatButton: {
    backgroundColor: '#07C160',
  },
  textButton: {
    backgroundColor: '#007AFF',
  },
  voiceButton: {
    backgroundColor: '#FF9500',
  },
  shareButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  vipButton: {
    backgroundColor: '#FFD700',
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
  },
  vipButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
