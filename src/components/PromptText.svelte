<script lang="ts">
  export let raw: string;

  type Segment = { t: 'text' | 'green' | 'red' | 'u'; v: string };

  function segments(s: string): Segment[] {
    const parts: Segment[] = [];
    const re = /<(green|red|u)>([^<]+)/gi;
    let cursor = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(s)) !== null) {
      if (m.index > cursor) parts.push({ t: 'text', v: s.slice(cursor, m.index) });
      parts.push({ t: m[1] as 'green' | 'red' | 'u', v: m[2].trim() });
      cursor = m.index + m[0].length;
      // skip malformed or well-formed closing tag if present at cursor
      const cl = /<\/?(green|red|u)>/gi;
      cl.lastIndex = cursor;
      const clm = cl.exec(s);
      if (clm && clm.index === cursor) cursor += clm[0].length;
    }
    if (cursor < s.length) parts.push({ t: 'text', v: s.slice(cursor) });
    return parts;
  }

  $: segs = segments(raw);
</script>

{#each segs as seg}{#if seg.t === 'green'}<span class="green">{seg.v}</span>{:else if seg.t === 'red'}<span class="red">{seg.v}</span>{:else if seg.t === 'u'}<span class="underline">{seg.v}</span>{:else}{seg.v}{/if}{/each}
