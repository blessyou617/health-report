// questionnaire.js
const app = getApp();

Page({
  data: {
    formData: {
      smoking: 'no',
      alcohol: 'no',
      sleepTime: '',
      exercise: 'never',
      medicalHistory: ''
    }
  },

  bindSleepChange(e) {
    this.setData({
      'formData.sleepTime': e.detail.value
    });
  },

  submitQuestionnaire(e) {
    const formData = e.detail.value;
    
    // Validate required fields
    if (!formData.smoking) {
      wx.showToast({ title: '请选择吸烟情况', icon: 'none' });
      return;
    }
    
    wx.showLoading({ title: '上传中...' });
    
    // Upload file first
    const filePath = app.globalData.uploadFilePath;
    
    if (!filePath) {
      wx.hideLoading();
      wx.showToast({ title: '请先上传文件', icon: 'none' });
      return;
    }
    
    // Upload file to server
    app.uploadFile(filePath).then(res => {
      const reportId = res.report_id;
      app.globalData.reportId = reportId;
      
      // Submit questionnaire
      return app.request({
        url: `${app.globalData.baseUrl}/questionnaire/submit`,
        method: 'POST',
        data: {
          report_id: reportId,
          questionnaire_data: JSON.stringify(formData)
        }
      });
    }).then(res => {
      wx.hideLoading();
      
      // Navigate to analysis page
      wx.redirectTo({
        url: `/pages/loading/loading?id=${app.globalData.reportId}`
      });
    }).catch(err => {
      wx.hideLoading();
      wx.showToast({
        title: err.message || '提交失败',
        icon: 'none'
      });
    });
  }
});
