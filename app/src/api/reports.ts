import { request } from './client';

export type ReportStatus =
  | 'uploaded'
  | 'questionnaire_submitted'
  | 'analyzing'
  | 'analysis_ready'
  | 'analysis_failed';

export type ReportResponse = {
  id: number;
  user_id: number;
  file_name: string;
  file_type: string;
  file_url: string;
  report_text?: string | null;
  questionnaire_data?: string | null;
  analysis_result?: string | null;
  status: ReportStatus;
  is_unlocked: boolean;
  created_at: string;
  updated_at: string;
};

export async function getReport(reportId: number, token?: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/report/${reportId}`, { token });
}
