// index.js
const app = getApp();

Page({
  data: {
    recentReports: []
  },

  onShow() {
    // Load recent reports
    this.loadRecentReports();
  },

  goToUpload() {
    wx.navigateTo({
      url: '/pages/upload/upload'
    });
  },

  viewReport(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/report/report?id=${id}`
    });
  },

  loadRecentReports() {
    // Mock data for demo
    this.setData({
      recentReports: [
        { id: 1, date: '2026-03-01', status: 'completed', statusText: '已完成' },
        { id: 2, date: '2026-02-15', status: 'completed', statusText: '已完成' }
      ]
    });
    
    // Real API call:
    /*
    app.request({
      url: `${app.globalData.baseUrl}/reports`,
      method: 'GET',
      success: res => {
        this.setData({ recentReports: res.data });
      }
    });
    */
  }
});
