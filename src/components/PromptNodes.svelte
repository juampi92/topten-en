<script lang="ts">
  import { TAG_CLASS, type PromptNode } from '../lib/promptText';
  export let nodes: PromptNode[];
</script>

{#each nodes as node}
  {#if node.type === 'text'}{node.value}
  {:else}<span class={TAG_CLASS[node.name]}><svelte:self nodes={node.children} /></span>
  {/if}
{/each}
