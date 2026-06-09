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
  finalState: string | null;
  observedAt: string | null;
};

export type PatrolObservation = {
  observationId: number;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  finalState: string | null;
  analysisStatus: string;
  analysisNotes: string | null;
  observedAt: string | null;
};

export type PatrolPlantAnalysis = {
  patrolId: string;
  plantGroupCode: string;
  representativePlantQr: string;
  finalState: string;
  summary: string;
  evidenceCount: number;
  lastObservedAt: string | null;
  evidenceImages: PatrolEvidenceImage[];
  observations: PatrolObservation[];
};

export type PatrolAnalysis = {
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
