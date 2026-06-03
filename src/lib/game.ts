import type { CardMap, GameState } from './types';

export const STORAGE_KEY = 'topten.v3';

export const DEFAULT_STATE: GameState = {
  deck: [],
  drawn: [],
  current: null,
  revealed: false,
  initialized: false,
};

export function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function freshDeck(cards: CardMap): number[] {
  return shuffle(Object.keys(cards).map(Number));
}

export function loadState(): GameState | null {
  try {
    const r = localStorage.getItem(STORAGE_KEY);
    return r ? (JSON.parse(r) as GameState) : null;
  } catch {
    return null;
  }
}

export function saveState(s: GameState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {}
}
