import api from "./axiosInstance";

export type AnalisisRequest = {
  imagenBase64: string;
  mimeType: string;
  observacionesOperador: string;
};

export const analizarPlanta = (payload: AnalisisRequest) =>
  api.post("/analisis/planta", payload).then((res) => res.data.data);
