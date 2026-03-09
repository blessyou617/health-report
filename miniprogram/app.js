// app.js
App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'https://your-api-domain.com/api/v1',
    reportId: null,
    analysisResult: null
  },

  onLaunch() {
    // Check login status
    this.checkLogin();
  },

  // WeChat login
  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: res => {
          if (res.code) {
            // Send code to backend
            wx.request({
              url: `${this.globalData.baseUrl}/auth/login`,
              method: 'POST',
              data: { code: res.code },
              success: res => {
                if (res.data.access_token) {
                  this.globalData.token = res.data.access_token;
                  this.globalData.userInfo = res.data.user;
                  wx.setStorageSync('token', res.data.access_token);
                  resolve(res.data);
                } else {
                  reject(new Error('Login failed'));
                }
              },
              fail: reject
            });
          } else {
            reject(new Error('Failed to get code'));
          }
        },
        fail: reject
      });
    });
  },

  // Check if logged in
  checkLogin() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
    }
  },

  // Make authenticated request
  request(options) {
    const token = this.globalData.token;
    const header = options.header || {};
    
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }
    
    return wx.request({
      ...options,
      header
    });
  },

  // Upload file
  uploadFile(filePath) {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${this.globalData.baseUrl}/upload/report`,
        filePath: filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${this.globalData.token}`
        },
        success: res => {
          const data = JSON.parse(res.data);
          if (data.report_id) {
            resolve(data);
          } else {
            reject(new Error(data.detail || 'Upload failed'));
          }
        },
        fail: reject
      });
    });
  }
});
