<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  export let totalDrawn;
  const dispatch = createEventDispatcher();
</script>

<div class="deck-empty">
  <div class="marquee"><span class="one">1</span> · <span class="ten">10</span></div>
  <h3>End of the deck</h3>
  <p>You went through all {totalDrawn} cards. Reshuffle or browse the drawn pile.</p>
  <button class="btn-restart" on:click={() => dispatch('restart')}>Reshuffle</button>
  <button
    class="action"
    style="flex: none; padding: 10px 18px; margin-top: 4px; background: transparent; color: var(--card-ink-soft)"
    on:click={() => dispatch('viewDrawn')}
  >
    View drawn pile
  </button>
</div>
