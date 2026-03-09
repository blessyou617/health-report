import * as WeChat from 'react-native-wechat';

const WECHAT_APP_ID = 'your_wechat_app_id'; // TODO: 替换为你的微信 App ID

export const initWeChat = async (): Promise<boolean> => {
  try {
    await WeChat.registerApp(WECHAT_APP_ID);
    return true;
  } catch (error) {
    console.error('WeChat init failed:', error);
    return false;
  }
};

export const isWeChatInstalled = async (): Promise<boolean> => {
  try {
    return await WeChat.isWXAppInstalled();
  } catch {
    return false;
  }
};

export interface ShareContent {
  title: string;
  description: string;
  thumbUrl?: string;
  webpageUrl?: string;
  text?: string;
  type: 'text' | 'image' | 'webpage';
}

export const shareToWeChat = async (content: ShareContent): Promise<boolean> => {
  try {
    const isInstalled = await isWeChatInstalled();
    if (!isInstalled) {
      throw new Error('微信未安装');
    }

    let message: any = {
      type: content.type === 'text' ? WeChat.TypeText : WeChat.TypeWebpage,
    };

    if (content.type === 'text') {
      message = {
        ...message,
        text: content.text,
      };
    } else {
      message = {
        ...message,
        title: content.title,
        description: content.description,
        webpageUrl: content.webpageUrl,
        thumbUrl: content.thumbUrl,
      };
    }

    const result = await WeChat.shareToSession(message);
    return result.errCode === 0;
  } catch (error) {
    console.error('Share to WeChat failed:', error);
    return false;
  }
};

// 微信支付
export interface PayParams {
  partnerId: string;
  prepayId: string;
  nonceStr: string;
  timeStamp: number;
  sign: string;
}

export const wechatPay = async (params: PayParams): Promise<boolean> => {
  try {
    const result = await WeChat.pay({
      partnerId: params.partnerId,
      prepayId: params.prepayId,
      nonceStr: params.nonceStr,
      timeStamp: params.timeStamp,
      sign: params.sign,
    });
    return result.errCode === 0;
  } catch (error) {
    console.error('WeChat Pay failed:', error);
    return false;
  }
};

// 生成报告分享内容
export const generateShareContent = (reportData: any): ShareContent => {
  const { date, score, advice } = reportData;
  
  const text = `📊 我的健康报告 (${date})

健康评分: ${score}/100

${advice.slice(0, 100)}...

——由健康报告 App 生成`;

  return {
    title: '我的健康报告',
    description: `健康评分: ${score}/100`,
    text,
    type: 'text',
  };
};
