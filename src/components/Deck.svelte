<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import FlipCard from './FlipCard.svelte';
  import type { Card } from '../lib/types';

  export let deckCount: number;
  export let card: Card;
  export let revealed: boolean;
  export let dealing: boolean;
  export let discarding: boolean;

  const dispatch = createEventDispatcher();

  $: layers = Math.max(0, deckCount);
</script>

<div class="deck">
  <div class="deck-layer l3{layers < 3 ? ' empty' : ''}">
    <div class="mini-back" />
  </div>
  <div class="deck-layer l2{layers < 2 ? ' empty' : ''}">
    <div class="mini-back" />
  </div>
  <div class="deck-layer l1{layers < 1 ? ' empty' : ''}">
    <div class="mini-back" />
  </div>
  {#if card}
    <FlipCard {card} {revealed} {dealing} {discarding} on:tap />
  {/if}
</div>
