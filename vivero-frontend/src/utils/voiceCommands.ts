import { RobotSearchState, SearchStartOrientation } from "../api/robotApi";

export type ParsedVoiceCommand =
  | { kind: "navigate"; path: string; summary: string }
  | { kind: "robot_mode"; mode: "AUTO_LINE" | "MANUAL_FREE" | "ACRO"; summary: string; path: string }
  | { kind: "robot_stop"; summary: string; path: string }
  | { kind: "robot_camera"; camera: "FRONT" | "LEFT" | "RIGHT"; summary: string; path: string }
  | { kind: "robot_search_state"; state: RobotSearchState; orientation: SearchStartOrientation; summary: string; path: string }
  | { kind: "robot_goto"; targetPlantQr: string; orientation: SearchStartOrientation; summary: string; path: string }
  | { kind: "robot_speed"; profile: "LOW" | "MEDIUM" | "HIGH" | "TURBO"; summary: string; path: string };

const sequenceSeparatorPattern = /\b(?:y luego|despues|luego|then)\b/;

const pathCommands: Array<[string, string, string]> = [
  ["dashboard", "/dashboard", "Abrir dashboard"],
  ["plantas", "/plants", "Abrir plantas"],
  ["patrullajes", "/patrols", "Abrir patrullajes"],
  ["reportes", "/reports", "Abrir reportes"],
  ["analisis", "/analisis", "Abrir analisis"],
  ["usuarios", "/users", "Abrir usuarios"],
  ["robot", "/robot", "Abrir robot"],
  ["control del robot", "/robot", "Abrir robot"],
];

function normalizeText(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\w\s:/.-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function resolveOrientation(text: string): SearchStartOrientation {
  return /(extremo opuesto|reversa|reverse|invertido)/.test(text) ? "REVERSE" : "FORWARD";
}

function resolveState(text: string): RobotSearchState | null {
  if (/(peligro|danger)/.test(text)) return "PELIGRO";
  if (/(atencion|attention)/.test(text)) return "ATENCION";
  if (/(sano|healthy)/.test(text)) return "SANO";
  if (/(inconclusa|inconcluso|unknown)/.test(text)) return "INCONCLUSA";
  return null;
}

function resolveQrLabel(text: string): string | null {
  const directMatch = text.match(/pla[_\s-]*(\d+)[_\s-]*ma[_\s-]*(\d+)[_\s-]*(iz|dr|izquierda|derecha)/i);
  if (directMatch) {
    const side = directMatch[3].toLowerCase().startsWith("iz") ? "IZ" : "DR";
    return `PLA_${directMatch[1]}_MA_${directMatch[2]}_${side}`;
  }

  const semanticMatch = text.match(/planta\s+(\d+).*maceta\s+(\d+).*(izquierda|derecha|iz|dr)/i);
  if (!semanticMatch) {
    return null;
  }
  const side = semanticMatch[3].toLowerCase().startsWith("iz") ? "IZ" : "DR";
  return `PLA_${semanticMatch[1]}_MA_${semanticMatch[2]}_${side}`;
}

export function parseVoiceCommand(rawText: string): ParsedVoiceCommand | null {
  const text = normalizeText(rawText);
  return parseNormalizedVoiceCommand(text);
}

function parseNormalizedVoiceCommand(text: string): ParsedVoiceCommand | null {
  if (!text) return null;

  for (const [keyword, path, summary] of pathCommands) {
    if (text === keyword || text.includes(`abrir ${keyword}`) || text.includes(`ir a ${keyword}`) || text.includes(`ve a ${keyword}`)) {
      return { kind: "navigate", path, summary };
    }
  }

  if (/(modo manual|control manual|manual)/.test(text)) {
    return { kind: "robot_mode", mode: "MANUAL_FREE", summary: "Cambiar a modo manual", path: "/robot" };
  }
  if (/(modo auto|modo automatico|auto)/.test(text)) {
    return { kind: "robot_mode", mode: "AUTO_LINE", summary: "Cambiar a modo automatico", path: "/robot" };
  }
  if (/(acro|acrobacia)/.test(text)) {
    return { kind: "robot_mode", mode: "ACRO", summary: "Ejecutar acrobacia", path: "/robot" };
  }
  if (/(detener|alto|stop|frenar)/.test(text)) {
    return { kind: "robot_stop", summary: "Detener robot", path: "/robot" };
  }

  if (/(camara frontal|camara frente)/.test(text)) {
    return { kind: "robot_camera", camera: "FRONT", summary: "Cambiar a camara frontal", path: "/robot" };
  }
  if (/camara izquierda/.test(text)) {
    return { kind: "robot_camera", camera: "LEFT", summary: "Cambiar a camara izquierda", path: "/robot" };
  }
  if (/camara derecha/.test(text)) {
    return { kind: "robot_camera", camera: "RIGHT", summary: "Cambiar a camara derecha", path: "/robot" };
  }

  if (/(potencia baja|perfil bajo|velocidad baja|low)/.test(text)) {
    return { kind: "robot_speed", profile: "LOW", summary: "Cambiar a potencia baja", path: "/robot" };
  }
  if (/(potencia media|perfil medio|velocidad media|medium)/.test(text)) {
    return { kind: "robot_speed", profile: "MEDIUM", summary: "Cambiar a potencia media", path: "/robot" };
  }
  if (/(potencia alta|perfil alto|velocidad alta|high)/.test(text)) {
    return { kind: "robot_speed", profile: "HIGH", summary: "Cambiar a potencia alta", path: "/robot" };
  }
  if (/(potencia turbo|perfil turbo|velocidad turbo|turbo)/.test(text)) {
    return { kind: "robot_speed", profile: "TURBO", summary: "Cambiar a potencia turbo", path: "/robot" };
  }

  if (/buscar.*estado/.test(text)) {
    const state = resolveState(text);
    if (state) {
      return {
        kind: "robot_search_state",
        state,
        orientation: resolveOrientation(text),
        summary: `Buscar por estado ${state}`,
        path: "/robot",
      };
    }
  }

  if (/(buscar planta|ir a planta|goto planta|buscar qr)/.test(text)) {
    const targetPlantQr = resolveQrLabel(text);
    if (targetPlantQr) {
      return {
        kind: "robot_goto",
        targetPlantQr,
        orientation: resolveOrientation(text),
        summary: `Buscar ${targetPlantQr}`,
        path: "/robot",
      };
    }
  }

  return null;
}

export function parseVoiceCommandSequence(rawText: string): ParsedVoiceCommand[] {
  const normalizedText = normalizeText(rawText);
  if (!normalizedText) {
    return [];
  }

  const segments = normalizedText
    .split(sequenceSeparatorPattern)
    .map((segment) => segment.trim())
    .filter(Boolean)
    .slice(0, 3);

  if (segments.length <= 1) {
    const singleCommand = parseNormalizedVoiceCommand(normalizedText);
    return singleCommand ? [singleCommand] : [];
  }

  const parsedSegments = segments
    .map((segment) => parseNormalizedVoiceCommand(segment))
    .filter((command): command is ParsedVoiceCommand => command !== null);

  if (parsedSegments.length !== segments.length) {
    const singleCommand = parseNormalizedVoiceCommand(normalizedText);
    return singleCommand ? [singleCommand] : [];
  }

  return parsedSegments;
}
