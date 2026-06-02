<script lang="ts">
  import { onMount } from 'svelte';
  import { CARDS } from './data/cards';
  import { DEFAULT_STATE, freshDeck, loadState, saveState } from './lib/game';
  import type { GameState } from './lib/types';

  import Welcome from './components/Welcome.svelte';
  import Deck from './components/Deck.svelte';
  import DeckEmpty from './components/DeckEmpty.svelte';
  import DrawnSheet from './components/DrawnSheet.svelte';
  import SettingsSheet from './components/SettingsSheet.svelte';

  import IconHome from './icons/IconHome.svelte';
  import IconStack from './icons/IconStack.svelte';
  import IconNext from './icons/IconNext.svelte';
  import IconDown from './icons/IconDown.svelte';

  let state: GameState = { ...DEFAULT_STATE };
  let hydrated = false;
  let screen = 'welcome';
  let openSheet: string | null = null;
  let dealing = false;
  let discarding = false;
  let countBump = false;
  let lockRef = false;

  // Load persisted state on mount
  onMount(() => {
    const loaded = loadState();
    if (loaded) {
      state = {
        ...DEFAULT_STATE,
        ...loaded,
        settings: { ...DEFAULT_STATE.settings, ...(loaded.settings || {}) },
      };
    }
    hydrated = true;
  });

  // Persist state whenever it changes (only after hydration)
  $: if (hydrated) saveState(state);

  // Apply font size to <html>
  $: document.documentElement.setAttribute('data-fontsize', state.settings.fontSize);

  $: hasActiveGame = state.current !== null || state.drawn.length > 0;

  function startFreshGame() {
    const deck = freshDeck(CARDS);
    const next = deck.pop() ?? null;
    state = { ...state, deck, drawn: [], current: next, revealed: false, initialized: true };
    screen = 'deck';
    discarding = false;
    dealing = true;
    setTimeout(() => { dealing = false; }, 600);
  }

  function continueGame() {
    screen = 'deck';
  }

  function onCardTap() {
    if (lockRef) return;
    if (state.current === null) return;
    if (state.revealed) {
      // Face-up card: tap is intentionally a no-op to prevent accidental discards.
      return;
    }
    reveal();
  }

  function reveal() {
    if (lockRef) return;
    if (state.current === null) return;
    if (state.revealed) return;
    state = { ...state, revealed: true };
    lockRef = true;
    setTimeout(() => { lockRef = false; }, 720);
  }

  function advance() {
    if (lockRef) return;
    lockRef = true;
    discarding = true;
    setTimeout(() => {
      if (state.current !== null) {
        const newDrawn = [...state.drawn, state.current];
        const newDeck = state.deck.slice();
        const next = newDeck.length ? newDeck.pop() : null;
        state = { ...state, drawn: newDrawn, deck: newDeck, current: next, revealed: false };
      }
      discarding = false;
      dealing = true;
      countBump = true;
      setTimeout(() => { countBump = false; }, 550);
      setTimeout(() => { dealing = false; }, 600);
      lockRef = false;
    }, 500);
  }

  function handleClearAndReshuffle() {
    openSheet = null;
    startFreshGame();
  }

  function updateSettings(newSettings: GameState['settings']) {
    state = { ...state, settings: newSettings };
  }

  $: cardsTotal = Object.keys(CARDS).length;
  $: deckRemaining = state.deck.length;

</script>

<div class="app-shell">
  {#if screen === 'welcome'}
    <Welcome
      drawnCount={state.drawn.length}
      totalCards={cardsTotal}
      hasGame={hasActiveGame}
      onStart={startFreshGame}
      onContinue={continueGame}
      onOpenSettings={() => { openSheet = 'settings'; }}
    />

    {#if openSheet === 'settings'}
      <SettingsSheet
        settings={state.settings}
        on:change={(e) => updateSettings(e.detail)}
        on:close={() => { openSheet = null; }}
      />
    {/if}

  {:else}
    <div class="topbar">
      <button class="icon-btn" on:click={() => { screen = 'welcome'; }} aria-label="Home">
        <IconHome width="20" height="20" />
      </button>
      <div class="title">TopTen</div>
      <div class="counter">{state.drawn.length} / {cardsTotal}</div>
    </div>

    <div class="deck-screen" data-screen-label="02 Deck">
      <div class="card-stage">
        {#if state.current === null}
          <DeckEmpty
            totalDrawn={state.drawn.length}
            on:restart={startFreshGame}
            on:viewDrawn={() => { openSheet = 'drawn'; }}
          />
        {:else}
          {#key state.current + ':' + state.drawn.length}
            <Deck
              deckCount={deckRemaining}
              card={CARDS[state.current]}
              revealed={state.revealed}
              {dealing}
              {discarding}
              on:tap={onCardTap}
              on:discard={advance}
            />
          {/key}
        {/if}
      </div>

      <div class="deck-actions">
        <button class="action" on:click={() => { openSheet = 'drawn'; }}>
          <IconStack />
          <span class="label">DRAWN</span>
          <span class="count{countBump ? ' bump' : ''}">{state.drawn.length}</span>
        </button>
        <button
          class="action primary"
          on:click={advance}
          disabled={state.current === null || !state.revealed}
          style={(state.current === null || !state.revealed) ? 'opacity: 0.4; pointer-events: none' : ''}
          aria-label="Discard card"
        >
          <IconDown />
          <span class="label">DISCARD</span>
        </button>
        <button
          class="action primary"
          on:click={reveal}
          disabled={state.current === null || state.revealed}
          style={(state.current === null || state.revealed) ? 'opacity: 0.4; pointer-events: none' : ''}
          aria-label="Draw card"
        >
          <IconNext />
          <span class="label">DRAW</span>
        </button>
      </div>
    </div>

    {#if openSheet === 'drawn'}
      <DrawnSheet
        drawn={state.drawn}
        cards={CARDS}
        on:close={() => { openSheet = null; }}
        on:clear={handleClearAndReshuffle}
      />
    {/if}
    {#if openSheet === 'settings'}
      <SettingsSheet
        settings={state.settings}
        on:change={(e) => updateSettings(e.detail)}
        on:close={() => { openSheet = null; }}
      />
    {/if}
  {/if}

</div>
