<script lang="ts">
  import { parsePrompt } from '../lib/promptText';
  import PromptNodes from './PromptNodes.svelte';

  export let raw: string;

  $: nodes = parsePrompt(raw);
</script>

<PromptNodes nodes={nodes} />
