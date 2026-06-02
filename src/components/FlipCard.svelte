<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import CardPromptCarousel from './CardPromptCarousel.svelte';
  import type { Card } from '../lib/types';

  export let card: Card;
  export let revealed: boolean;
  export let dealing: boolean;
  export let discarding: boolean;

  const dispatch = createEventDispatcher();

  $: classes = [
    'card-3d',
    revealed ? 'is-flipped' : '',
    dealing ? 'is-dealing' : '',
    discarding ? 'is-discarding' : '',
  ].filter(Boolean).join(' ');
</script>

<div
  class={classes}
  on:click={() => dispatch('tap')}
  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && dispatch('tap')}
  role="button"
  tabindex="0"
  aria-label={revealed ? 'Tap to draw next' : 'Tap to reveal'}
>
  <div class="card-face card-back" aria-hidden={revealed}>
    <div class="card-back-emblem">
      <span class="lockup">Top<span class="ten">Ten</span></span>
      <div class="ornament" aria-hidden="true">
        <span class="pip low" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip" />
        <span class="pip high" />
      </div>
    </div>
    {#if !revealed && !discarding}
      <div class="tap-hint">Tap to reveal</div>
    {/if}
  </div>

  <div class="card-face card-front" aria-hidden={!revealed && !discarding}>
    <div class="card-prompt-area">
      <CardPromptCarousel prompts={card.prompts} />
    </div>
  </div>
</div>
