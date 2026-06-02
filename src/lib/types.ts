export interface Card {
  id: number;
  prompts: string[]; // raw strings — <low>…</low> / <high>…</high> inline
}

export type CardMap = Record<number, Card>;

export interface GameSettings {
  fontSize: string;
}

export interface GameState {
  deck: number[];
  drawn: number[];
  current: number | null;
  revealed: boolean;
  settings: GameSettings;
  initialized: boolean;
}
