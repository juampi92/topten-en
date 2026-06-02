<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let title;
  export let message;
  export let confirmLabel;

  const dispatch = createEventDispatcher();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="sheet center" on:click={() => dispatch('cancel')}>
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="confirm-card" on:click|stopPropagation>
    <h3>{title}</h3>
    <p>{message}</p>
    <div class="confirm-actions">
      <button class="cancel" on:click={() => dispatch('cancel')}>Cancel</button>
      <button class="confirm" on:click={() => dispatch('confirm')}>{confirmLabel}</button>
    </div>
  </div>
</div>
