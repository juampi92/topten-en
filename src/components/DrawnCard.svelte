<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import IconClose from '../icons/IconClose.svelte';
  import CardPromptCarousel from './CardPromptCarousel.svelte';
  import type { Card } from '../lib/types';

  export let card: Card;
  const dispatch = createEventDispatcher();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="card-overlay" on:click={() => dispatch('close')}></div>
<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="card-modal" on:click|stopPropagation>
  <button class="card-modal-close" on:click={() => dispatch('close')} aria-label="Close">
    <IconClose width="18" height="18" />
  </button>
  <div class="card-prompt-area">
    <CardPromptCarousel prompts={card.prompts} />
  </div>
</div>
