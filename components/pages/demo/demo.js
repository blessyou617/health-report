// pages/demo/demo.js
Page({
  data: {
    report: {
      summary: '您的体检报告显示整体健康状况良好。部分指标需要注意，建议调整饮食结构并加强运动。",
      abnormal_items: [
        '血清甘油三酯偏高 (1.85 mmol/L)',
        '轻度脂肪肝',
        '尿酸偏高 (432 μmol/L)'
      ],
      normal_items: [
        '血常规各项指标正常',
        '肝功能全部正常',
        '肾功能正常',
        '空腹血糖正常',
        '心电图正常',
        '血压正常'
      ],
      lifestyle_advice: '建议减少高脂饮食，增加有氧运动。每周至少运动3次，每次30分钟以上。少熬夜，保证充足睡眠。定期复查血脂和尿酸。'
    }
  },

  onLoad() {},

  // 语音播放
  onVoicePlay(e) {
    const { playing, type } = e.detail;
    console.log('语音播放:', type, playing);
    
    if (playing) {
      // 调用语音播放
      wx.showToast({ title: '正在生成语音...', icon: 'none' });
    }
  },

  // 点击异常指标
  onAbnormalItemTap(e) {
    const { index, item } = e.detail;
    console.log('点击异常指标:', index, item);
    
    wx.showModal({
      title: '指标详情',
      content: item,
      showCancel: false
    });
  },

  // 分享
  onShare() {
    wx.showShareMenu();
  },

  // 追问
  onAskQuestion() {
    wx.navigateTo({
      url: '/pages/chat/chat?id=1'
    });
  }
});
