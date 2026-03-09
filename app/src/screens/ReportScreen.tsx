import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Share, ActivityIndicator } from 'react-native';
import { RouteProp, useFocusEffect, useRoute } from '@react-navigation/native';

import { generateTextReport } from '../services/reportShare';
import { getReport, ReportResponse } from '../api/reports';
import { generateReportTTS } from '../api/tts';

type ReportRouteParams = {
  Report: {
    reportId?: number;
    token?: string;
  };
};

type ReportAnalysisView = {
  summary: string;
  abnormalItems: string[];
  normalItems: string[];
  lifestyleAdvice: string;
};

type AudioState = 'idle' | 'loading' | 'playing' | 'paused' | 'completed' | 'error' | 'unavailable';

type PlaybackStatus = {
  isLoaded: boolean;
  error?: string;
  didJustFinish?: boolean;
  isPlaying?: boolean;
};

type AudioSoundInstance = {
  unloadAsync: () => Promise<unknown>;
  setOnPlaybackStatusUpdate: (callback: ((status: PlaybackStatus) => void) | null) => void;
  playAsync: () => Promise<unknown>;
  pauseAsync: () => Promise<unknown>;
};

type AudioModule = {
  Sound: {
    createAsync: (
      source: { uri: string },
      initialStatus: { shouldPlay: boolean },
      onPlaybackStatusUpdate: (status: PlaybackStatus) => void
    ) => Promise<{ sound: AudioSoundInstance }>;
  };
};

function parseAnalysis(report: ReportResponse): ReportAnalysisView {
  const fallbackSummary = '报告已上传，等待分析结果。';

  if (!report.analysis_result) {
    return {
      summary: fallbackSummary,
      abnormalItems: [],
      normalItems: [],
      lifestyleAdvice: '',
    };
  }

  try {
    const parsed = JSON.parse(report.analysis_result);
    return {
      summary: parsed?.summary || fallbackSummary,
      abnormalItems: Array.isArray(parsed?.abnormal_items) ? parsed.abnormal_items : [],
      normalItems: Array.isArray(parsed?.normal_items) ? parsed.normal_items : [],
      lifestyleAdvice: parsed?.lifestyle_advice || '',
    };
  } catch {
    return {
      summary: report.analysis_result,
      abnormalItems: [],
      normalItems: [],
      lifestyleAdvice: '',
    };
  }
}

export default function ReportScreen() {
  const route = useRoute<RouteProp<ReportRouteParams, 'Report'>>();
  const reportId = route.params?.reportId;
  const token = route.params?.token;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);

  const [audioState, setAudioState] = useState<AudioState>('idle');
  const [audioError, setAudioError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const soundRef = useRef<AudioSoundInstance | null>(null);

  const getAudioModule = useCallback(async (): Promise<AudioModule | null> => {
    try {
      const module = await import('expo-av');
      return module.Audio as unknown as AudioModule;
    } catch {
      setAudioState('unavailable');
      setAudioError('当前环境不支持语音播放，请使用最新 Expo Go 或重新构建客户端。');
      return null;
    }
  }, []);

  const unloadAudio = useCallback(async () => {
    if (soundRef.current) {
      try {
        await soundRef.current.unloadAsync();
      } catch {
        // ignore
      } finally {
        soundRef.current.setOnPlaybackStatusUpdate(null);
        soundRef.current = null;
      }
    }
  }, []);

  useEffect(() => {
    return () => {
      void unloadAudio();
    };
  }, [unloadAudio]);

  const onPlaybackStatusUpdate = useCallback((status: PlaybackStatus) => {
    if (!status.isLoaded) {
      if (status.error) {
        setAudioState('error');
        setAudioError('音频播放失败，请稍后重试。');
      }
      return;
    }

    if (status.didJustFinish) {
      setAudioState('completed');
      return;
    }

    setAudioState(status.isPlaying ? 'playing' : 'paused');
  }, []);

  const ensureAudioUrl = useCallback(async (): Promise<string | null> => {
    if (!reportId || !token) {
      setAudioState('unavailable');
      setAudioError('缺少登录信息，暂无法生成语音。');
      return null;
    }

    if (audioUrl) {
      return audioUrl;
    }

    setAudioState('loading');
    setAudioError(null);

    try {
      const tts = await generateReportTTS(reportId, token, true);
      if (!tts.audio_url) {
        setAudioState('unavailable');
        setAudioError('语音文件暂不可用，请稍后再试。');
        return null;
      }

      setAudioUrl(tts.audio_url);
      setAudioState('idle');
      return tts.audio_url;
    } catch (e) {
      setAudioState('error');
      setAudioError(e instanceof Error ? e.message : '语音生成失败');
      return null;
    }
  }, [audioUrl, reportId, token]);

  const handlePlayAudio = useCallback(async () => {
    const targetUrl = await ensureAudioUrl();
    if (!targetUrl) return;

    const Audio = await getAudioModule();
    if (!Audio) return;

    setAudioError(null);

    try {
      if (!soundRef.current) {
        const { sound } = await Audio.Sound.createAsync(
          { uri: targetUrl },
          { shouldPlay: true },
          onPlaybackStatusUpdate
        );
        soundRef.current = sound;
      } else {
        await soundRef.current.playAsync();
      }
      setAudioState('playing');
    } catch {
      setAudioState('error');
      setAudioError('音频加载失败，请稍后重试。');
    }
  }, [ensureAudioUrl, getAudioModule, onPlaybackStatusUpdate]);

  const handlePauseAudio = useCallback(async () => {
    if (!soundRef.current) return;
    try {
      await soundRef.current.pauseAsync();
      setAudioState('paused');
    } catch {
      setAudioState('error');
      setAudioError('暂停失败，请重试。');
    }
  }, []);

  const handleShareAudioLink = useCallback(async () => {
    const targetUrl = await ensureAudioUrl();
    if (!targetUrl) {
      Alert.alert('提示', '当前无可分享音频链接');
      return;
    }

    await Share.share({
      title: '健康报告语音播报',
      message: `健康报告语音播报链接：${targetUrl}`,
    });

    // NOTE: 微信转发后直接收听依赖后端返回“长期有效或可签名访问”的 HTTPS audio_url。
  }, [ensureAudioUrl]);

  const loadReport = useCallback(async () => {
    if (!reportId) {
      setReport(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getReport(reportId, token);
      setReport(data);
    } catch (e) {
      const message = e instanceof Error ? e.message : '加载报告失败';
      setError(message);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [reportId, token]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  useFocusEffect(
    useCallback(() => {
      loadReport();
      return () => {
        void unloadAudio();
      };
    }, [loadReport, unloadAudio])
  );

  const analysis = useMemo(() => (report ? parseAnalysis(report) : null), [report]);

  const reportDataForShare = useMemo(
    () => ({
      date: report ? new Date(report.updated_at).toLocaleDateString('zh-CN') : new Date().toLocaleDateString('zh-CN'),
      score: analysis?.abnormalItems.length ? Math.max(60, 100 - analysis.abnormalItems.length * 5) : 85,
      indicators: [
        { name: '报告状态', value: report?.status || 'unknown' },
        { name: '异常指标数量', value: String(analysis?.abnormalItems.length || 0) },
        { name: '正常指标数量', value: String(analysis?.normalItems.length || 0) },
        { name: '是否解锁', value: report?.is_unlocked ? '已解锁' : '未解锁' },
      ],
      advice: analysis?.lifestyleAdvice || '请根据医生建议保持规律作息和健康饮食。',
    }),
    [analysis, report]
  );

  const handleShareText = async () => {
    try {
      const text = generateTextReport(reportDataForShare);
      await Share.share({ message: text, title: '健康报告' });
    } catch {
      Alert.alert('分享失败', '请重试');
    }
  };

  const handleWechatShare = () => {
    Alert.alert('微信分享', '请先在设置中绑定微信账号', [{ text: '确定' }]);
  };

  const handlePayment = () => {
    Alert.alert('解锁完整报告', '¥9.9 解锁 AI 详细分析和语音报告', [
      { text: '取消', style: 'cancel' },
      { text: '微信支付', onPress: () => Alert.alert('提示', '请接入支付接口后调用 /payment/create') },
    ]);
  };

  if (!reportId) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyTitle}>暂无报告</Text>
        <Text style={styles.emptySubtitle}>请先上传并分析一份体检报告</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#07C160" />
        <Text style={styles.loadingText}>报告加载中...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>加载失败</Text>
        <Text style={styles.errorSubtitle}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadReport}>
          <Text style={styles.retryButtonText}>重试</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!report || !analysis) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyTitle}>报告为空</Text>
        <Text style={styles.emptySubtitle}>未查询到报告数据</Text>
      </View>
    );
  }

  const isReady = report.status === 'analysis_ready';
  const isLocked = !report.is_unlocked;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.date}>{new Date(report.updated_at).toLocaleDateString('zh-CN')}</Text>
        <Text style={styles.title}>健康报告</Text>
      </View>

      {!isReady ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⏳ 报告状态</Text>
          <View style={styles.card}>
            <Text style={styles.normalText}>当前状态：{report.status}</Text>
            <Text style={styles.normalText}>报告暂未完成，请稍后刷新查看。</Text>
            <TouchableOpacity style={[styles.shareButton, styles.textButton]} onPress={loadReport}>
              <Text style={styles.shareButtonText}>刷新状态</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🩺 健康总结</Text>
            <View style={styles.card}>
              <Text style={styles.adviceText}>{analysis.summary || '暂无总结'}</Text>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🏥 异常指标</Text>
            <View style={styles.card}>
              {analysis.abnormalItems.length ? (
                analysis.abnormalItems.map((item, index) => (
                  <View key={`${item}-${index}`} style={styles.indicatorRow}>
                    <Text style={styles.indicatorName}>{item}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.normalText}>暂无异常指标</Text>
              )}
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🔊 语音播报</Text>
            <View style={styles.card}>
              {isLocked ? (
                <Text style={styles.normalText}>解锁完整报告后可收听语音播报</Text>
              ) : (
                <>
                  <Text style={styles.normalText}>语音内容为适合老年人收听的精简摘要（健康总结、异常提醒、生活建议）。</Text>
                  <View style={styles.audioActions}>
                    <TouchableOpacity
                      style={[styles.shareButton, styles.voiceButton]}
                      onPress={handlePlayAudio}
                      disabled={audioState === 'loading'}
                    >
                      <Text style={styles.shareButtonText}>播放</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.shareButton, styles.textButton]}
                      onPress={handlePauseAudio}
                      disabled={audioState !== 'playing'}
                    >
                      <Text style={styles.shareButtonText}>暂停</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.shareButton, styles.wechatButton]}
                      onPress={handleShareAudioLink}
                    >
                      <Text style={styles.shareButtonText}>分享语音链接（预留）</Text>
                    </TouchableOpacity>
                  </View>

                  {audioState === 'loading' && <Text style={styles.audioHint}>音频加载中...</Text>}
                  {audioState === 'playing' && <Text style={styles.audioHint}>播放中</Text>}
                  {audioState === 'paused' && <Text style={styles.audioHint}>已暂停</Text>}
                  {audioState === 'completed' && <Text style={styles.audioHint}>播放完成</Text>}
                  {audioState === 'unavailable' && <Text style={styles.errorSubtitle}>音频不可用，请稍后重试。</Text>}
                  {audioState === 'error' && <Text style={styles.errorSubtitle}>{audioError || '语音播报失败'}</Text>}
                </>
              )}
            </View>
          </View>

          {isLocked ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>🔒 完整报告未解锁</Text>
              <View style={styles.card}>
                <Text style={styles.normalText}>您当前可查看免费摘要。支付后可查看完整正常指标、生活建议及追问能力。</Text>
                <TouchableOpacity style={styles.vipButton} onPress={handlePayment}>
                  <Text style={styles.vipButtonText}>💎 解锁完整 AI 报告 (¥9.9)</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <>
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>💪 正常指标</Text>
                <View style={styles.card}>
                  {analysis.normalItems.length ? (
                    analysis.normalItems.map((item, index) => (
                      <View key={`${item}-${index}`} style={styles.indicatorRow}>
                        <Text style={styles.indicatorName}>{item}</Text>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.normalText}>暂无正常指标</Text>
                  )}
                </View>
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>💡 生活建议</Text>
                <View style={styles.card}>
                  <Text style={styles.adviceText}>{analysis.lifestyleAdvice || '暂无建议'}</Text>
                </View>
              </View>
            </>
          )}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📤 分享报告</Text>
            <View style={styles.shareButtons}>
              <TouchableOpacity style={[styles.shareButton, styles.wechatButton]} onPress={handleWechatShare}>
                <Text style={styles.shareButtonText}>💬 微信好友</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.shareButton, styles.textButton]} onPress={handleShareText}>
                <Text style={styles.shareButtonText}>📝 文字分享</Text>
              </TouchableOpacity>
            </View>
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    color: '#666',
    fontSize: 15,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#d93025',
    marginBottom: 8,
  },
  errorSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
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
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
  },
  indicatorRow: {
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  indicatorName: {
    fontSize: 16,
    color: '#333',
  },
  normalText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  adviceText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 24,
  },
  audioActions: {
    marginTop: 10,
    gap: 10,
  },
  audioHint: {
    marginTop: 10,
    color: '#333',
    fontSize: 14,
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
    marginTop: 10,
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
    textAlign: 'center',
  },
  vipButton: {
    backgroundColor: '#FFD700',
    padding: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  vipButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
