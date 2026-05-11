import api from "./axiosInstance";

export const getPatrols = () => api.get("/patrols").then((res) => res.data.data);

export type PatrolEvidenceImage = {
  observationId: number;
  imageId: number;
  imageUrl: string;
  mimeType: string;
  sortOrder: number;
  relevant: boolean;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  finalState: string;
  observedAt: string;
};

export type PatrolObservation = {
  observationId: number;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  finalState: string;
  analysisStatus: string;
  analysisNotes: string | null;
  observedAt: string;
  images: Array<{
    id: number;
    mimeType: string;
    sortOrder: number;
    relevant: boolean;
    imageUrl: string;
  }>;
};

export type PatrolPlantAnalysis = {
  patrolId: string;
  plantGroupCode: string;
  representativePlantQr: string;
  finalState: string;
  summary: string;
  evidenceCount: number;
  lastObservedAt: string;
  sides: Array<{
    side: string;
    dominantState: string;
    evidenceCount: number;
  }>;
  evidenceImages: PatrolEvidenceImage[];
  observations: PatrolObservation[];
};

export type PatrolAnalysisResponse = {
  robotId: string;
  patrolId: string;
  totalGroups: number;
  healthyCount: number;
  attentionCount: number;
  dangerCount: number;
  manualReviewCount: number;
  inconclusiveCount: number;
  plants: PatrolPlantAnalysis[];
};

export const getPatrolAnalysis = (patrolId: string) =>
  api.get(`/robot/patrols/${patrolId}/analysis`).then((res) => res.data.data as PatrolAnalysisResponse);
