import rawData from '../../data/cards_en.json';
import type { CardMap } from '../lib/types';

export const CARDS: CardMap = Object.fromEntries(
  rawData.cards.map(c => [c.id, { id: c.id, prompts: c.prompts }])
);
