import { describe, it, expect } from 'vitest';
import { parsePrompt, PROMPT_TAGS, TAG_CLASS, type PromptNode } from './promptText';

describe('parsePrompt', () => {
  it('returns a single text node for plain text without tags', () => {
    expect(parsePrompt('just a plain prompt')).toEqual<PromptNode[]>([
      { type: 'text', value: 'just a plain prompt' },
    ]);
  });

  it('parses a single non-nested green tag', () => {
    expect(parsePrompt('FOO <green>BAR</green> BAZ')).toEqual<PromptNode[]>([
      { type: 'text', value: 'FOO ' },
      { type: 'tag', name: 'green', children: [{ type: 'text', value: 'BAR' }] },
      { type: 'text', value: ' BAZ' },
    ]);
  });

  it('handles card 30 nested green→u→green (regression)', () => {
    const input =
      "SAY A WORD FROM THE DICTIONARY: FROM <green>ONE THAT <u>CAP'TEN</u> NEVER USES</green> TO <red>ONE HE ALWAYS SAYS</red>.";
    expect(parsePrompt(input)).toEqual<PromptNode[]>([
      { type: 'text', value: 'SAY A WORD FROM THE DICTIONARY: FROM ' },
      {
        type: 'tag', name: 'green', children: [
          { type: 'text', value: 'ONE THAT ' },
          { type: 'tag', name: 'u', children: [{ type: 'text', value: "CAP'TEN" }] },
          { type: 'text', value: ' NEVER USES' },
        ],
      },
      { type: 'text', value: ' TO ' },
      { type: 'tag', name: 'red', children: [{ type: 'text', value: 'ONE HE ALWAYS SAYS' }] },
      { type: 'text', value: '.' },
    ]);
  });

  it('builds a three-level tree for green→u→red→u→green', () => {
    expect(parsePrompt('<green>A<u>B<red>C</red>D</u>E</green>')).toEqual<PromptNode[]>([
      {
        type: 'tag', name: 'green', children: [
          { type: 'text', value: 'A' },
          {
            type: 'tag', name: 'u', children: [
              { type: 'text', value: 'B' },
              { type: 'tag', name: 'red', children: [{ type: 'text', value: 'C' }] },
              { type: 'text', value: 'D' },
            ],
          },
          { type: 'text', value: 'E' },
        ],
      },
    ]);
  });

  it('emits the tail as a child of an unclosed opening tag', () => {
    expect(parsePrompt('hello <green>world')).toEqual<PromptNode[]>([
      { type: 'text', value: 'hello ' },
      { type: 'tag', name: 'green', children: [{ type: 'text', value: 'world' }] },
    ]);
  });

  it('ignores stray closing tags and coalesces the surrounding text', () => {
    expect(parsePrompt('foo</green>bar')).toEqual<PromptNode[]>([
      { type: 'text', value: 'foobar' },
    ]);
  });

  it('preserves literal ">" characters inside a tag', () => {
    expect(parsePrompt('<green>A>B</green>')).toEqual<PromptNode[]>([
      { type: 'tag', name: 'green', children: [{ type: 'text', value: 'A>B' }] },
    ]);
  });

  it('matches tags case-insensitively and normalizes the name to lowercase', () => {
    expect(parsePrompt('<GREEN>x</GREEN>')).toEqual<PromptNode[]>([
      { type: 'tag', name: 'green', children: [{ type: 'text', value: 'x' }] },
    ]);
  });
});

describe('registry', () => {
  it('lists every supported tag and maps it to a CSS class', () => {
    expect(PROMPT_TAGS).toEqual(['green', 'red', 'u']);
    expect(TAG_CLASS).toEqual({ green: 'green', red: 'red', u: 'underline' });
  });
});
