import api from "./axiosInstance";

export type AnalisisRequest = {
  imagenBase64: string;
  mimeType: string;
  observacionesOperador: string;
};

export type AnalysisImageRequest = {
  imagenBase64: string;
  mimeType: string;
};

export type ManualAnalysisRequest = {
  images: AnalysisImageRequest[];
  generalLabels: string[];
  exactLabels: string[];
  estadoGeneral: string;
  urgencia: string;
  reporteManual: string;
  confianza?: number;
  hallazgos?: string[];
  recomendaciones?: string[];
  operatorNotes?: string;
  patrolId?: number;
  createStandaloneReport?: boolean;
  reportTitle?: string;
};

export type AnalysisHistoryItem = {
  id: number;
  sourceType: string;
  estadoGeneral: string;
  urgencia: string;
  confianza: number;
  summaryText: string;
  operatorNotes?: string | null;
  hallazgos: string[];
  recomendaciones: string[];
  patrolId?: number | null;
  reportId?: number | null;
  reportTitle?: string | null;
  generalLabels: string[];
  exactLabels: string[];
  images: { id: number; imageUrl: string; mimeType: string; sortOrder: number }[];
  createdAt: string;
};

export const analizarPlanta = (payload: AnalisisRequest) =>
  api.post("/analisis/planta", payload).then((res) => res.data.data);

export const createManualAnalysis = (payload: ManualAnalysisRequest) =>
  api.post("/analisis/manual", payload).then((res) => res.data.data as AnalysisHistoryItem);

export const getAnalysisHistory = () =>
  api.get("/analisis/history").then((res) => res.data.data as AnalysisHistoryItem[]);
