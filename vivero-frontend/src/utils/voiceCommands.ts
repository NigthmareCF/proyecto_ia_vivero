import { RobotSearchState, SearchStartOrientation } from "../api/robotApi";

export type ParsedVoiceCommand =
  | { kind: "navigate"; path: string; summary: string }
  | { kind: "robot_mode"; mode: "AUTO_LINE" | "MANUAL_FREE" | "ACRO"; summary: string; path: string }
  | { kind: "robot_stop"; summary: string; path: string }
  | { kind: "robot_move"; direction: "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT"; summary: string; path: string }
  | { kind: "robot_camera"; camera: "FRONT" | "LEFT" | "RIGHT"; summary: string; path: string }
  | { kind: "robot_search_state"; state: RobotSearchState; orientation: SearchStartOrientation; summary: string; path: string }
  | { kind: "robot_goto"; targetPlantQr: string; orientation: SearchStartOrientation; summary: string; path: string }
  | { kind: "robot_speed"; profile: "LOW" | "MEDIUM" | "HIGH" | "TURBO"; summary: string; path: string }
  | { kind: "robot_speed_custom"; percent: number; summary: string; path: string };

const sequenceSeparatorPattern = /\b(?:y luego|despues|luego|then)\b/;
const looseJoinerPattern = /^(?:y|e|con|por favor)\b\s*/;
const fillerWordsPattern = /\b(?:por favor|porfa|favor|el|la|de|del|al)\b/g;

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
    .replace(fillerWordsPattern, " ")
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

type CommandMatch = {
  command: ParsedVoiceCommand;
  start: number;
  end: number;
  priority: number;
};

type CommandMatcher = (text: string) => CommandMatch | null;

function buildMatch(command: ParsedVoiceCommand, match: RegExpExecArray, priority: number): CommandMatch {
  return {
    command,
    start: match.index,
    end: match.index + match[0].length,
    priority,
  };
}

function sanitizeRemainingText(text: string) {
  return text
    .replace(sequenceSeparatorPattern, " ")
    .replace(looseJoinerPattern, "")
    .replace(/\s+/g, " ")
    .trim();
}

function resolveCustomSpeed(text: string): number | null {
  const match = text.match(
    /(?:potencia|perfil|velocidad|modo)?\s*custom\s*(?:a|al|de)?\s*(\d{1,3})|(?:potencia|velocidad|pwm)\s*(\d{1,3})/i,
  );
  const rawValue = match?.[1] ?? match?.[2];
  if (!rawValue) return null;
  const value = Number(rawValue);
  if (!Number.isFinite(value)) return null;
  return Math.min(100, Math.max(0, value));
}

const commandMatchers: CommandMatcher[] = [
  (text) => {
    const match = /(buscar planta|ir a planta|goto planta|buscar qr)\s+.+/.exec(text);
    if (!match) return null;
    const targetPlantQr = resolveQrLabel(match[0]);
    if (!targetPlantQr) return null;
    return buildMatch(
      {
        kind: "robot_goto",
        targetPlantQr,
        orientation: resolveOrientation(match[0]),
        summary: `Buscar ${targetPlantQr}`,
        path: "/robot",
      },
      match,
      0,
    );
  },
  (text) => {
    const match = /buscar(?: por)? estado\s+.+/.exec(text);
    if (!match) return null;
    const state = resolveState(match[0]);
    if (!state) return null;
    return buildMatch(
      {
        kind: "robot_search_state",
        state,
        orientation: resolveOrientation(match[0]),
        summary: `Buscar por estado ${state}`,
        path: "/robot",
      },
      match,
      1,
    );
  },
  (text) => {
    const customSpeed = resolveCustomSpeed(text);
    if (customSpeed === null) return null;
    const match = /(?:(?:potencia|perfil|velocidad|modo)?\s*custom\s*(?:a|al|de)?\s*\d{1,3}|(?:potencia|velocidad|pwm)\s*\d{1,3})/i.exec(
      text,
    );
    if (!match) return null;
    return buildMatch(
      {
        kind: "robot_speed_custom",
        percent: customSpeed,
        summary: `Aplicar potencia custom ${customSpeed}%`,
        path: "/robot",
      },
      match,
      2,
    );
  },
  (text) => {
    const match = /(potencia baja|perfil bajo|velocidad baja|low)\b/.exec(text);
    return match
      ? buildMatch({ kind: "robot_speed", profile: "LOW", summary: "Cambiar a potencia baja", path: "/robot" }, match, 3)
      : null;
  },
  (text) => {
    const match = /(potencia media|perfil medio|velocidad media|medium)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_speed", profile: "MEDIUM", summary: "Cambiar a potencia media", path: "/robot" },
          match,
          4,
        )
      : null;
  },
  (text) => {
    const match = /(potencia alta|perfil alto|velocidad alta|high)\b/.exec(text);
    return match
      ? buildMatch({ kind: "robot_speed", profile: "HIGH", summary: "Cambiar a potencia alta", path: "/robot" }, match, 5)
      : null;
  },
  (text) => {
    const match = /(potencia turbo|perfil turbo|velocidad turbo|turbo)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_speed", profile: "TURBO", summary: "Cambiar a potencia turbo", path: "/robot" },
          match,
          6,
        )
      : null;
  },
  (text) => {
    const match = /(camara frontal|camara frente|camara front|camara principal)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_camera", camera: "FRONT", summary: "Cambiar a camara frontal", path: "/robot" },
          match,
          7,
        )
      : null;
  },
  (text) => {
    const match = /(camara izquierda|camara iz|camara left)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_camera", camera: "LEFT", summary: "Cambiar a camara izquierda", path: "/robot" },
          match,
          8,
        )
      : null;
  },
  (text) => {
    const match = /(camara derecha|camara dr|camara right)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_camera", camera: "RIGHT", summary: "Cambiar a camara derecha", path: "/robot" },
          match,
          9,
        )
      : null;
  },
  (text) => {
    const match = /(modo manual|control manual|manual)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_mode", mode: "MANUAL_FREE", summary: "Cambiar a modo manual", path: "/robot" },
          match,
          10,
        )
      : null;
  },
  (text) => {
    const match = /(modo auto|modo automatico|automatico|auto)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_mode", mode: "AUTO_LINE", summary: "Cambiar a modo automatico", path: "/robot" },
          match,
          11,
        )
      : null;
  },
  (text) => {
    const match = /(acro|acrobacia)\b/.exec(text);
    return match
      ? buildMatch({ kind: "robot_mode", mode: "ACRO", summary: "Ejecutar acrobacia", path: "/robot" }, match, 12)
      : null;
  },
  (text) => {
    const match = /(detener|alto|stop|frenar)\b/.exec(text);
    return match ? buildMatch({ kind: "robot_stop", summary: "Detener robot", path: "/robot" }, match, 13) : null;
  },
  (text) => {
    const match = /(avanzar|adelante|frente)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_move", direction: "FORWARD", summary: "Mover robot hacia adelante", path: "/robot" },
          match,
          14,
        )
      : null;
  },
  (text) => {
    const match = /(retroceder|atras|reversa)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_move", direction: "BACKWARD", summary: "Mover robot hacia atras", path: "/robot" },
          match,
          15,
        )
      : null;
  },
  (text) => {
    const match = /(girar izquierda|mover izquierda|izquierda)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_move", direction: "LEFT", summary: "Mover robot a la izquierda", path: "/robot" },
          match,
          16,
        )
      : null;
  },
  (text) => {
    const match = /(girar derecha|mover derecha|derecha)\b/.exec(text);
    return match
      ? buildMatch(
          { kind: "robot_move", direction: "RIGHT", summary: "Mover robot a la derecha", path: "/robot" },
          match,
          17,
        )
      : null;
  },
  (text) => {
    for (const [keyword, path, summary] of pathCommands) {
      const match = new RegExp(`(?:^|\\b)(?:abrir|ir a|ve a)?\\s*${keyword}(?:\\b|$)`).exec(text);
      if (match) {
        return buildMatch({ kind: "navigate", path, summary }, match, 20);
      }
    }
    return null;
  },
];

function extractCommandsFromText(text: string): ParsedVoiceCommand[] {
  const commands: ParsedVoiceCommand[] = [];
  let remainingText = text;

  for (let index = 0; index < 6 && remainingText; index += 1) {
    const candidateMatches = commandMatchers
      .map((matcher) => matcher(remainingText))
      .filter((match): match is CommandMatch => match !== null)
      .sort((left, right) => left.start - right.start || left.priority - right.priority || right.end - left.end);

    const nextMatch = candidateMatches[0];
    if (!nextMatch) {
      break;
    }

    commands.push(nextMatch.command);
    remainingText = sanitizeRemainingText(
      `${remainingText.slice(0, nextMatch.start)} ${remainingText.slice(nextMatch.end)}`,
    );
  }

  return commands;
}

function parseNormalizedVoiceCommand(text: string): ParsedVoiceCommand | null {
  if (!text) return null;

  return extractCommandsFromText(text)[0] ?? null;
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
    .slice(0, 6);

  if (segments.length <= 1) {
    return extractCommandsFromText(normalizedText);
  }

  const parsedSegments = segments
    .flatMap((segment) => extractCommandsFromText(segment));

  if (parsedSegments.length === 0) {
    const singleCommand = parseNormalizedVoiceCommand(normalizedText);
    return singleCommand ? [singleCommand] : [];
  }

  return parsedSegments;
}
