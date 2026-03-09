// chat.js
const app = getApp();

Page({
  data: {
    reportId: null,
    messages: [],
    inputText: '',
    sending: false,
    remaining: 2,
    scrollIntoView: 'bottom'
  },

  onLoad(options) {
    const reportId = options.id;
    this.setData({ reportId });
    
    this.loadQAHistory(reportId);
  },

  onUnload() {
    // Stop audio if playing
    if (this.innerAudioContext) {
      this.innerAudioContext.stop();
    }
  },

  loadQAHistory(reportId) {
    app.request({
      url: `${app.globalData.baseUrl}/qa/status/${reportId}`,
      method: 'GET',
      success: res => {
        const history = res.data.history || [];
        const messages = [];
        
        history.forEach(qa => {
          messages.push({
            id: qa.id,
            role: 'user',
            content: qa.question
          });
          messages.push({
            id: qa.id + '_a',
            role: 'ai',
            content: qa.answer
          });
        });
        
        this.setData({
          messages,
          remaining: res.data.remaining
        });
      }
    });
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value });
  },

  sendMessage() {
    const question = this.data.inputText.trim();
    if (!question || this.data.sending) return;
    
    // Add user message
    const messages = [...this.data.messages, {
      id: Date.now(),
      role: 'user',
      content: question
    }];
    
    this.setData({
      messages,
      inputText: '',
      sending: true,
      scrollIntoView: 'bottom'
    });
    
    // Send to API
    app.request({
      url: `${app.globalData.baseUrl}/qa/ask`,
      method: 'POST',
      data: {
        report_id: this.data.reportId,
        question: question
      },
      success: res => {
        const answer = res.data.answer;
        
        // Add AI response
        this.setData({
          messages: [...this.data.messages, {
            id: res.data.qa_id,
            role: 'ai',
            content: answer
          }],
          remaining: res.data.remaining,
          sending: false,
          scrollIntoView: 'bottom'
        });
        
        // Scroll to bottom
        setTimeout(() => {
          this.setData({ scrollIntoView: 'bottom' });
        }, 100);
      },
      fail: err => {
        wx.showToast({
          title: err.data?.detail || '发送失败',
          icon: 'none'
        });
        this.setData({ sending: false });
      }
    });
  },

  goBack() {
    wx.navigateBack();
  }
});
