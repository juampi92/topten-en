export const PROMPT_TAGS = ['green', 'red', 'u'] as const;
export type PromptTag = (typeof PROMPT_TAGS)[number];

export const TAG_CLASS: Record<PromptTag, string> = {
  green: 'green',
  red: 'red',
  u: 'underline',
};

export type TextNode = { type: 'text'; value: string };
export type TagNode = { type: 'tag'; name: PromptTag; children: PromptNode[] };
export type PromptNode = TextNode | TagNode;

const TAG_RE = new RegExp(`<\\/?(${PROMPT_TAGS.join('|')})>`, 'gi');

export function parsePrompt(input: string): PromptNode[] {
  const root: PromptNode[] = [];
  const stack: PromptNode[][] = [root];
  const top = () => stack[stack.length - 1];

  const pushText = (s: string) => {
    if (!s) return;
    const c = top();
    const last = c[c.length - 1];
    if (last && last.type === 'text') last.value += s;
    else c.push({ type: 'text', value: s });
  };

  let cursor = 0;
  let m: RegExpExecArray | null;
  TAG_RE.lastIndex = 0;
  while ((m = TAG_RE.exec(input)) !== null) {
    if (m.index > cursor) pushText(input.slice(cursor, m.index));
    const isClose = input[m.index + 1] === '/';
    const name = m[1].toLowerCase() as PromptTag;
    if (isClose) {
      if (stack.length > 1) stack.pop();
    } else {
      const node: TagNode = { type: 'tag', name, children: [] };
      top().push(node);
      stack.push(node.children);
    }
    cursor = m.index + m[0].length;
  }
  if (cursor < input.length) pushText(input.slice(cursor));
  return root;
}
