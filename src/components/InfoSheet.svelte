<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import IconClose from '../icons/IconClose.svelte';

  const dispatch = createEventDispatcher();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div class="sheet" on:click={() => dispatch('close')}>
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="sheet-panel" on:click|stopPropagation>
    <div class="sheet-handle" />
    <div class="sheet-header">
      <h2>About this project</h2>
      <button class="sheet-close" on:click={() => dispatch('close')} aria-label="Close">
        <IconClose width="18" height="18" />
      </button>
    </div>
    <div class="sheet-body">
      <div class="setting-group">
        <div class="label">What this is</div>
        <div class="setting-info">
          <b>TopTen - EN</b> is the English translation of the prompts for the party game
          <b><a
            href="https://boardgamegeek.com/boardgame/300905/top-ten"
            target="_blank"
            rel="noopener noreferrer"
          >TopTen</a></b>. It's not a replacement for the original: you still need a copy of
          the game (in any language) for its number cards (1–10) and the base rules. This
          app just gives you the English prompts so you can play with English-speaking friends.
        </div>
      </div>

      <div class="setting-group">
        <div class="label">Source &amp; contribute</div>
        <div class="setting-info">
          The code and translations live on GitHub. Spotted a bad translation or want to
          improve the app? Open an issue or send a pull request! Contributions are very
          welcome.
          <br /><br />
          <a
            href="https://github.com/juampi92/topten-en"
            target="_blank"
            rel="noopener noreferrer"
          >github.com/juampi92/topten-en</a>
        </div>
      </div>
    </div>
  </div>
</div>
