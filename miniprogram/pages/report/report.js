// report.js
const app = getApp();

Page({
  data: {
    reportId: null,
    report: {
      date: '',
      summary: '',
      abnormal_items: [],
      normal_items: [],
      lifestyle_advice: ''
    },
    remainingQuestions: 2,
    isPlayingSummary: false,
    isPlayingAdvice: false,
    audioContext: null
  },

  onLoad(options) {
    const reportId = options.id;
    this.setData({ reportId });
    
    this.loadReport(reportId);
  },

  loadReport(reportId) {
    wx.showLoading({ title: '加载中...' });
    
    app.request({
      url: `${app.globalData.baseUrl}/report/${reportId}`,
      method: 'GET',
      success: res => {
        wx.hideLoading();
        
        const data = res.data;
        let analysis = {};
        
        try {
          analysis = JSON.parse(data.analysis_result);
        } catch (e) {
          analysis = { summary: data.analysis_result };
        }
        
        this.setData({
          report: {
            date: new Date(data.created_at).toLocaleDateString(),
            summary: analysis.summary || '',
            abnormal_items: analysis.abnormal_items || [],
            normal_items: analysis.normal_items || [],
            lifestyle_advice: analysis.lifestyle_advice || ''
          }
        });
        
        // Load Q&A status
        this.loadQAStatus(reportId);
      },
      fail: err => {
        wx.hideLoading();
        wx.showToast({ title: '加载失败', icon: 'none' });
      }
    });
  },

  loadQAStatus(reportId) {
    app.request({
      url: `${app.globalData.baseUrl}/qa/status/${reportId}`,
      method: 'GET',
      success: res => {
        this.setData({
          remainingQuestions: res.data.remaining
        });
      }
    });
  },

  // Voice playback functions
  playSummaryVoice() {
    this.playVoice('summary');
  },

  playAdviceVoice() {
    this.playVoice('advice');
  },

  playVoice(type) {
    const reportId = this.data.reportId;
    
    wx.showLoading({ title: '生成语音...' });
    
    app.request({
      url: `${app.globalData.baseUrl}/tts/report/${reportId}`,
      method: 'POST',
      data: { include_advice: type === 'advice' },
      success: res => {
        wx.hideLoading();
        
        const audioUrl = app.globalData.baseUrl.replace('/api/v1', '') + res.data.audio_url;
        
        this.data.audioContext = wx.createInnerAudioContext();
        this.data.audioContext.src = audioUrl;
        this.data.audioContext.play();
        
        if (type === 'summary') {
          this.setData({ isPlayingSummary: true });
        } else {
          this.setData({ isPlayingAdvice: true });
        }
        
        this.data.audioContext.onEnded(() => {
          this.setData({ isPlayingSummary: false, isPlayingAdvice: false });
        });
      },
      fail: err => {
        wx.hideLoading();
        wx.showToast({ title: '生成语音失败', icon: 'none' });
      }
    });
  },

  stopSummaryVoice() {
    this.stopVoice();
    this.setData({ isPlayingSummary: false });
  },

  stopAdviceVoice() {
    this.stopVoice();
    this.setData({ isPlayingAdvice: false });
  },

  stopVoice() {
    if (this.data.audioContext) {
      this.data.audioContext.stop();
      this.data.audioContext = null;
    }
  },

  goToChat() {
    if (this.data.remainingQuestions <= 0) {
      wx.showToast({
        title: '追问次数已用完',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: `/pages/chat/chat?id=${this.data.reportId}`
    });
  }
});
