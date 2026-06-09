export function fileToAnalysisImage(file: File) {
  return new Promise<{ mimeType: string; imagenBase64: string }>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      const [, payload] = result.split(",");
      if (!payload) {
        reject(new Error("No se pudo convertir la imagen a base64"));
        return;
      }
      resolve({ mimeType: file.type, imagenBase64: payload });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function splitListInput(value: string) {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}
