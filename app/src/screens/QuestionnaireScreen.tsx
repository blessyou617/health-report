import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';

const questions = [
  {
    id: 1,
    question: '您最近一周的平均睡眠时长是多少？',
    options: ['少于 5 小时', '5-6 小时', '7-8 小时', '超过 8 小时'],
  },
  {
    id: 2,
    question: '您每周运动几次？',
    options: ['几乎不', '1-2 次', '3-4 次', '5 次以上'],
  },
  {
    id: 3,
    question: '您目前的压力水平如何？',
    options: ['很低', '较低', '一般', '较高', '很高'],
  },
  {
    id: 4,
    question: '您每天平均喝多少水？',
    options: ['少于 1 杯', '1-3 杯', '4-6 杯', '7 杯以上'],
  },
  {
    id: 5,
    question: '您最近一个月有感冒或生病吗？',
    options: ['没有', '1 次', '2-3 次', '3 次以上'],
  },
];

export default function QuestionnaireScreen({ navigation }: any) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);

  const handleAnswer = (optionIndex: number) => {
    const newAnswers = [...answers, optionIndex];
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Submit
      Alert.alert(
        '提交成功',
        '感谢您完成问卷，报告生成中...',
        [
          {
            text: '查看报告',
            onPress: () => navigation.navigate('Report'),
          },
        ]
      );
    }
  };

  const question = questions[currentQuestion];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.progress}>
        <Text style={styles.progressText}>
          问题 {currentQuestion + 1} / {questions.length}
        </Text>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill, 
              { width: `${((currentQuestion + 1) / questions.length) * 100}%` }
            ]} 
          />
        </View>
      </View>

      <View style={styles.questionCard}>
        <Text style={styles.questionText}>{question.question}</Text>
        
        {question.options.map((option, index) => (
          <TouchableOpacity
            key={index}
            style={styles.optionButton}
            onPress={() => handleAnswer(index)}
          >
            <Text style={styles.optionText}>{option}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  progress: {
    padding: 20,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
  },
  questionCard: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 20,
    lineHeight: 26,
  },
  optionButton: {
    backgroundColor: '#f8f8f8',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  optionText: {
    fontSize: 16,
    color: '#333',
  },
});
