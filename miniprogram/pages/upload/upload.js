// upload.js
const app = getApp();

Page({
  data: {
    filePath: '',
    fileName: '',
    fileSize: ''
  },

  chooseFile() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['file'],
      sourceType: ['album', 'camera'],
      success: res => {
        const file = res.tempFiles[0];
        this.setData({
          filePath: file.tempFilePath,
          fileName: file.name || file.tempFilePath.split('/').pop(),
          fileSize: this.formatFileSize(file.size)
        });
        
        // Save to global data for next step
        app.globalData.uploadFilePath = file.tempFilePath;
      },
      fail: err => {
        wx.showToast({
          title: '选择文件失败',
          icon: 'none'
        });
      }
    });
  },

  removeFile() {
    this.setData({
      filePath: '',
      fileName: '',
      fileSize: ''
    });
    app.globalData.uploadFilePath = null;
  },

  formatFileSize(size) {
    if (size < 1024) {
      return size + ' B';
    } else if (size < 1024 * 1024) {
      return (size / 1024).toFixed(1) + ' KB';
    } else {
      return (size / (1024 * 1024)).toFixed(1) + ' MB';
    }
  },

  goToQuestionnaire() {
    if (!this.data.filePath) {
      wx.showToast({
        title: '请先上传文件',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/questionnaire/questionnaire'
    });
  }
});
