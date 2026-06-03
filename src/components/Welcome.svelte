<script lang="ts">
  import IconInfo from '../icons/IconInfo.svelte';
  import IconArrow from '../icons/IconArrow.svelte';
  import IconShuffle from '../icons/IconShuffle.svelte';

  export let drawnCount;
  export let totalCards;
  export let hasGame;
  export let onStart;
  export let onContinue;
  export let onOpenInfo;
</script>

<div class="welcome" data-screen-label="01 Welcome">
  <div class="welcome-bg-shapes">
    <div class="blob b1" />
    <div class="blob b2" />
    <div class="blob b3" />
  </div>

  <div class="welcome-top">
    <button class="icon-btn" on:click={onOpenInfo} aria-label="About">
      <IconInfo width="20" height="20" />
    </button>
  </div>

  <div class="wordmark">
    <span class="word">Top<span class="ten">Ten</span></span>
  </div>

  <p class="tagline">
    The English translation for <a
      href="https://boardgamegeek.com/boardgame/300905/top-ten"
      target="_blank"
      rel="noopener noreferrer">TopTen</a
    >. It requires the base game!
  </p>

  <div class="welcome-cta">
    {#if hasGame}
      <button class="btn-primary" on:click={onContinue}>
        <span>Continue</span>
        <IconArrow width="20" height="20" />
      </button>
      <button class="btn-secondary" on:click={onStart}>
        <span>Fresh deck</span>
        <IconShuffle width="18" height="18" />
      </button>
    {:else}
      <button class="btn-primary" on:click={onStart}>
        <span>Shuffle &amp; Play</span>
        <IconArrow width="20" height="20" />
      </button>
    {/if}
  </div>

  <div class="welcome-footer-placeholder">
    {drawnCount}/{totalCards} drawn
  </div>
</div>
