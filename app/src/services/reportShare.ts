import * as Speech from 'expo-speech';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

export interface ReportData {
  date: string;
  score: number;
  indicators: {
    name: string;
    value: string;
  }[];
  advice: string;
}

// 生成语音报告
export const generateVoiceReport = async (reportData: ReportData): Promise<string | null> => {
  const { date, score, indicators, advice } = reportData;

  const text = `您的健康报告来了，日期是${date}。综合健康评分为${score}分。${score >= 80 ? '表现不错！' : score >= 60 ? '需要多加注意。' : '建议尽快改善。'}`;

  try {
    // 使用语音合成
    Speech.speak(text, {
      language: 'zh-CN',
      pitch: 1.0,
      rate: 0.9,
    });

    return text;
  } catch (error) {
    console.error('Voice report generation failed:', error);
    return null;
  }
};

// 生成文字报告
export const generateTextReport = (reportData: ReportData): string => {
  const { date, score, indicators, advice } = reportData;

  let report = `📊 健康报告 - ${date}

综合评分: ${score}/100

`;

  indicators.forEach((indicator) => {
    report += `${indicator.name}: ${indicator.value}\n`;
  });

  report += `\n💡 建议:\n${advice}`;

  return report;
};

// 分享报告
export const shareReport = async (reportData: ReportData, type: 'text' | 'voice'): Promise<boolean> => {
  const text = generateTextReport(reportData);

  // 使用系统分享
  if (await Sharing.isAvailableAsync()) {
    const uri = FileSystem.cacheDirectory + 'health_report.txt';
    await FileSystem.writeAsStringAsync(uri, text);
    await Sharing.shareAsync(uri, {
      mimeType: 'text/plain',
      dialogTitle: '分享健康报告',
    });
    return true;
  }

  return false;
};
