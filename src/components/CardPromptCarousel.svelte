<script lang="ts">
  import PromptText from './PromptText.svelte';

  export let prompts: string[];

  let page = 0;

  function chunk(arr: string[], size: number): string[][] {
    const out: string[][] = [];
    for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
    return out;
  }

  $: pages = chunk(prompts, 2);
</script>

<div class="carousel">
  <div class="carousel-viewport">
    <div class="carousel-track" style="transform: translateX(-{page * 100}%)">
      {#each pages as pagePrompts}
        <div class="carousel-page">
          {#each pagePrompts as prompt, i}
            {#if i > 0}<hr class="prompt-divider" />{/if}
            <p class="card-prompt"><PromptText raw={prompt} /></p>
          {/each}
        </div>
      {/each}
    </div>
  </div>
  {#if pages.length > 1}
    <div class="carousel-nav">
      <button
        class="carousel-btn"
        disabled={page === 0}
        on:click|stopPropagation={() => (page -= 1)}
        aria-label="Previous"
      >&#8592;</button>
      <span class="carousel-counter">{page + 1} / {pages.length}</span>
      <button
        class="carousel-btn"
        disabled={page === pages.length - 1}
        on:click|stopPropagation={() => (page += 1)}
        aria-label="Next"
      >&#8594;</button>
    </div>
  {/if}
</div>
