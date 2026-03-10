export type RootTabParamList = {
  Questionnaire: undefined;
  Report: {
    reportId?: number;
    token?: string;
  } | undefined;
  Chat: undefined;
};
