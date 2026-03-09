// components/abnormal-list/abnormal-list.js
Component({
  properties: {
    items: {
      type: Array,
      value: []
    }
  },

  data: {},

  methods: {
    onItemTap(e) {
      const index = e.currentTarget.dataset.index;
      const item = this.data.items[index];
      
      this.triggerEvent('itemtap', { index, item });
    }
  }
});
