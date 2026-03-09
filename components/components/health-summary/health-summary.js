// components/health-summary/health-summary.js
Component({
  properties: {
    summary: {
      type: String,
      value: ''
    },
    showVoiceButton: {
      type: Boolean,
      value: true
    }
  },

  data: {
    isPlaying: false
  },

  methods: {
    onVoicePlay() {
      this.setData({ isPlaying: !this.data.isPlaying });
      this.triggerEvent('voiceplay', { 
        playing: this.data.isPlaying,
        type: 'summary' 
      });
    }
  }
});
