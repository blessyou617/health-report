import { request } from './client';

export type ReportTTSResponse = {
  audio_url: string;
  filename: string;
  message: string;
};

export async function generateReportTTS(
  reportId: number,
  token?: string,
  includeAdvice: boolean = true
): Promise<ReportTTSResponse> {
  return request<ReportTTSResponse>(
    `/tts/report/${reportId}?include_advice=${includeAdvice ? 'true' : 'false'}`,
    {
      method: 'POST',
      token,
    }
  );
}
