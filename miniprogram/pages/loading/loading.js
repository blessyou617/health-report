// loading.js
const app = getApp();

Page({
  data: {
    reportId: null,
    progress: 0,
    progressText: '0%',
    currentStep: '读取体检报告文件...',
    steps: [
      '读取体检报告文件...',
      '识别报告内容...',
      '分析血液指标...',
      '生成健康建议...',
      '完成分析'
    ],
    timer: null
  },

  onLoad(options) {
    const reportId = options.id || app.globalData.reportId;
    this.setData({ reportId });
    
    // Start animation
    this.startProgress();
    
    // Trigger analysis
    this.triggerAnalysis(reportId);
  },

  onUnload() {
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
  },

  startProgress() {
    let progress = 0;
    const steps = this.data.steps;
    let stepIndex = 0;
    
    this.data.timer = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 100) progress = 100;
      
      // Update step text
      const newStepIndex = Math.floor((progress / 100) * (steps.length - 1));
      if (newStepIndex > stepIndex && stepIndex < steps.length - 1) {
        stepIndex = newStepIndex;
      }
      
      this.setData({
        progress: Math.floor(progress),
        progressText: Math.floor(progress) + '%',
        currentStep: steps[stepIndex]
      });
      
      if (progress >= 100) {
        clearInterval(this.data.timer);
      }
    }, 1000);
  },

  triggerAnalysis(reportId) {
    // Call API to analyze report
    app.request({
      url: `${app.globalData.baseUrl}/analyze/report/${reportId}`,
      method: 'POST',
      success: res => {
        // Analysis completed, navigate to report page
        setTimeout(() => {
          wx.redirectTo({
            url: `/pages/report/report?id=${reportId}`
          });
        }, 1500);
      },
      fail: err => {
        wx.showToast({
          title: '分析失败，请重试',
          icon: 'none'
        });
        setTimeout(() => {
          wx.navigateBack();
        }, 2000);
      }
    });
  },

  // Poll for analysis status
  pollStatus(reportId) {
    const checkStatus = () => {
      app.request({
        url: `${app.globalData.baseUrl}/report/${reportId}`,
        method: 'GET',
        success: res => {
          if (res.data.status === 'completed') {
            wx.redirectTo({
              url: `/pages/report/report?id=${reportId}`
            });
          } else if (res.data.status === 'failed') {
            wx.showToast({
              title: '分析失败',
              icon: 'none'
            });
          }
        }
      });
    };
    
    // Check every 3 seconds
    const timer = setInterval(checkStatus, 3000);
    
    // Save timer for cleanup
    this.setData({ timer });
  }
});
