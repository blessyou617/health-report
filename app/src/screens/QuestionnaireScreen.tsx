import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  ActivityIndicator,
} from 'react-native';

import { QuestionnaireData } from '../types/questionnaire';

const yesNoQuestions = [
  { id: 'smoking', label: '1 是否抽烟或接触二手烟' },
  { id: 'alcohol', label: '2 是否饮酒' },
  { id: 'late_sleep', label: '3 是否经常熬夜' },
  { id: 'long_term_medication', label: '4 是否长期服药' },
] as const;

type QuestionId = (typeof yesNoQuestions)[number]['id'];

const defaultForm: QuestionnaireData = {
  smoking: false,
  alcohol: false,
  late_sleep: false,
  long_term_medication: false,
  medical_history: '',
};

export default function QuestionnaireScreen({ navigation }: any) {
  const [form, setForm] = useState<QuestionnaireData>();
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched] = useState<Record<QuestionId, boolean>>({
    smoking: false,
    alcohol: false,
    late_sleep: false,
    long_term_medication: false,
  });

  // TODO: replace with real recent-report query result
  const recentReportId: number | null = 1;

  const handleViewRecentReport = () => {
    if (!recentReportId) {
      return;
    }
    navigation.navigate('Report', { reportId: recentReportId });
  };

  const handleUploadPress = () => {
    Alert.alert('上传体检报告', '上传功能待接入（支持 PDF / 图片）');
  };

  const handleSelect = (questionId: QuestionId, value: boolean) => {
    setForm((prev) => ({
      ...defaultForm,
      ...prev,
      [questionId]: value,
    }));
    setTouched((prev) => ({
      ...prev,
      [questionId]: true,
    }));
  };

  const handleMedicalHistoryChange = (value: string) => {
    setForm((prev) => ({
      ...defaultForm,
      ...prev,
      medical_history: value,
    }));
  };

  const handleSubmit = async () => {
    const missing = yesNoQuestions.some((q) => !touched[q.id]);

    if (missing) {
      Alert.alert('请先完成问卷', '请先回答所有必填问题后再提交。');
      return;
    }

    setSubmitting(true);
    try {
      console.log(form);
      // TODO: call submit API with form + uploaded report id
      await new Promise((resolve) => setTimeout(resolve, 700));
      const reportId = 1;
      navigation.navigate('Report', { reportId });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.pageContainer}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
        <View style={styles.headerCard}>
          <Text style={styles.headerTitle}>AI体检报告解读</Text>
          <Text style={styles.headerSubtitle}>上传体检报告</Text>
          <Text style={styles.headerSubtitle}>填写生活习惯问卷</Text>
          <Text style={styles.headerSubtitle}>AI生成解读报告</Text>
        </View>

        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>上传区域</Text>
          <TouchableOpacity style={styles.uploadButton} onPress={handleUploadPress}>
            <Text style={styles.uploadButtonText}>上传体检报告</Text>
          </TouchableOpacity>
          <Text style={styles.uploadHint}>支持：PDF、图片</Text>
        </View>

        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>问卷区域</Text>

          {yesNoQuestions.map((question) => {
            const selected = touched[question.id] ? form?.[question.id] : null;

            return (
              <View key={question.id} style={styles.questionCard}>
                <Text style={styles.questionLabel}>{question.label}</Text>
                <View style={styles.optionRow}>
                  <TouchableOpacity
                    style={[styles.optionButton, selected === true && styles.optionButtonSelected]}
                    onPress={() => handleSelect(question.id, true)}
                  >
                    <Text style={[styles.optionText, selected === true && styles.optionTextSelected]}>是</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.optionButton, selected === false && styles.optionButtonSelected]}
                    onPress={() => handleSelect(question.id, false)}
                  >
                    <Text style={[styles.optionText, selected === false && styles.optionTextSelected]}>否</Text>
                  </TouchableOpacity>
                </View>
              </View>
            );
          })}

          <View style={styles.questionCard}>
            <Text style={styles.questionLabel}>5 病史输入（可选）</Text>
            <TextInput
              style={styles.historyInput}
              value={form?.medical_history ?? ''}
              onChangeText={handleMedicalHistoryChange}
              placeholder="请输入既往病史、手术史、过敏史等（可选）"
              placeholderTextColor="#8a8a8a"
              multiline
              textAlignVertical="top"
            />
          </View>
        </View>

        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>最近报告</Text>
          {recentReportId ? (
            <TouchableOpacity style={styles.recentReportButton} onPress={handleViewRecentReport}>
              <Text style={styles.recentReportButtonText}>查看报告</Text>
            </TouchableOpacity>
          ) : (
            <Text style={styles.emptyReportText}>暂无报告。</Text>
          )}
        </View>
      </ScrollView>

      <View style={styles.footerBar}>
        <TouchableOpacity
          style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator color="#fff" />
              <Text style={styles.submitButtonText}>生成中...</Text>
            </View>
          ) : (
            <Text style={styles.submitButtonText}>提交问卷并生成报告</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  pageContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 110,
  },
  headerCard: {
    backgroundColor: '#EEF5FF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#D8E9FF',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1f2d3d',
    marginBottom: 10,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#334155',
    lineHeight: 26,
  },
  sectionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 18,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#222',
    marginBottom: 14,
  },
  uploadButton: {
    backgroundColor: '#007AFF',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  uploadHint: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  questionCard: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
  },
  questionLabel: {
    fontSize: 16,
    color: '#1f2937',
    marginBottom: 10,
    lineHeight: 24,
  },
  optionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  optionButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  optionButtonSelected: {
    backgroundColor: '#EEF5FF',
    borderColor: '#007AFF',
  },
  optionText: {
    fontSize: 16,
    color: '#444',
  },
  optionTextSelected: {
    color: '#005EC2',
    fontWeight: '600',
  },
  historyInput: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#333',
    backgroundColor: '#fff',
  },
  recentReportButton: {
    backgroundColor: '#F1F7FF',
    borderWidth: 1,
    borderColor: '#007AFF',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  recentReportButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '700',
  },
  emptyReportText: {
    color: '#666',
    fontSize: 16,
    lineHeight: 24,
  },
  footerBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  submitButton: {
    backgroundColor: '#007AFF',
    borderRadius: 10,
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.8,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '700',
  },
});
