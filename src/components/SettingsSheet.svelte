<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import IconClose from '../icons/IconClose.svelte';

  export let settings;

  const dispatch = createEventDispatcher();

  function setSize(s) {
    dispatch('change', { ...settings, fontSize: s });
  }

  const sizes = [
    ['sm', 'Aa', 's1'],
    ['md', 'Aa', 's2'],
    ['lg', 'Aa', 's3'],
    ['xl', 'Aa', 's4'],
  ];
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="sheet" on:click={() => dispatch('close')}>
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="sheet-panel" on:click|stopPropagation>
    <div class="sheet-handle" />
    <div class="sheet-header">
      <h2>Settings</h2>
      <button class="sheet-close" on:click={() => dispatch('close')} aria-label="Close">
        <IconClose width="18" height="18" />
      </button>
    </div>
    <div class="sheet-body">
      <div class="setting-group">
        <div class="label">Topic text size</div>
        <div class="size-options" role="radiogroup">
          {#each sizes as [k, l, c]}
            <button
              class={c}
              aria-pressed={settings.fontSize === k}
              on:click={() => setSize(k)}
            >{l}</button>
          {/each}
        </div>
      </div>
      <div class="setting-group">
        <div class="label">About</div>
        <div class="setting-info">
          <b>TopTen</b> — pocket deck for the ranking party game. Use the Tweaks panel (toolbar) to remix the look.
        </div>
      </div>
    </div>
  </div>
</div>
