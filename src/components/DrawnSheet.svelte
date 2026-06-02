<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import IconClose from '../icons/IconClose.svelte';
  import IconEmpty from '../icons/IconEmpty.svelte';
  import DrawnCard from './DrawnCard.svelte';
  import PromptText from './PromptText.svelte';
  import type { CardMap } from '../lib/types';

  export let drawn: number[];
  export let cards: CardMap;

  const dispatch = createEventDispatcher();

  let selectedId: number | null = null;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions a11y-no-static-element-interactions -->
<div
  class="sheet"
  on:click={() => dispatch('close')}
>
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="sheet-panel" on:click|stopPropagation>
    <div class="sheet-handle" />
    <div class="sheet-header">
      <h2>Drawn<span class="num">{drawn.length}</span></h2>
      <button class="sheet-close" on:click={() => dispatch('close')} aria-label="Close">
        <IconClose width="18" height="18" />
      </button>
    </div>
    <div class="sheet-body">
      {#if drawn.length === 0}
        <div class="drawn-empty">
          <IconEmpty width="56" height="56" />
          <div class="title">Nothing yet</div>
          <p>Drawn cards land here after you move on.</p>
        </div>
      {:else}
        <ul class="drawn-list">
          {#each drawn.slice().reverse() as id, position}
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <li class="drawn-row" on:click|stopPropagation={() => selectedId = id}>
              <span class="num">{drawn.length - position}</span>
              <span class="topic-text">
                {#each cards[id].prompts as prompt}
                  <span class="prompt-line"><PromptText raw={prompt} /></span>
                {/each}
              </span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
    {#if drawn.length > 0}
      <div class="sheet-footer">
        <button class="btn-danger" on:click={() => dispatch('clear')}>Clear &amp; reshuffle</button>
      </div>
    {/if}
  </div>

</div>

{#if selectedId !== null}
  <DrawnCard card={cards[selectedId]} on:close={() => selectedId = null} />
{/if}
