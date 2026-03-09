// components/lifestyle-advice/lifestyle-advice.js
Component({
  properties: {
    advice: {
      type: String,
      value: ''
    },
    showVoiceButton: {
      type: Boolean,
      value: true
    },
    showShareButton: {
      type: Boolean,
      value: true
    },
    showQuestionButton: {
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
        type: 'advice'
      });
    },
    
    onShare() {
      this.triggerEvent('share');
    },
    
    onAskQuestion() {
      this.triggerEvent('askquestion');
    }
  }
});
