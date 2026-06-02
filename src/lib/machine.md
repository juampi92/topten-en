# Deck State Machine

The TopTen deck is governed by a small, explicit state machine. The diagram
below documents the legal states and transitions, mirroring the implementation
in `src/App.svelte`.

```mermaid
stateDiagram-v2
    [*] --> idle_empty

    idle_empty: idle_empty
    note right of idle_empty
      No top card (current === null).
      Shown via DeckEmpty; player can
      Reshuffle or view the Drawn pile.
    end note

    idle_empty --> idle_unrevealed: RESHUFFLE

    idle_unrevealed: idle_unrevealed
    note right of idle_unrevealed
      Top card is face down.
      Actions:
        DRAW (tap card, or "Draw" button)
        -> idle_revealed
    end note

    idle_unrevealed --> idle_revealed: DRAW

    idle_revealed: idle_revealed
    note right of idle_revealed
      Top card is face up.
      Actions:
        DISCARD (swipe down, or "Discard" button)
        -> discarding
      Tapping the card in this state does
      nothing (no accidental discards).
    end note

    idle_revealed --> discarding: DISCARD

    discarding: discarding
    note right of discarding
      Brief animation: the top card flies
      off toward the Drawn pile. After the
      animation completes, the next card
      (if any) is dealt back into
      idle_unrevealed; otherwise the deck
      is exhausted and we move to
      idle_empty.
    end note

    discarding --> idle_unrevealed: DEAL_NEXT
    discarding --> idle_empty: DECK_EXHAUSTED

    idle_empty --> [*]
```

## Transition triggers

| Trigger         | Source           | Target              | UI surface                           |
| --------------- | ---------------- | ------------------- | ------------------------------------ |
| `RESHUFFLE`     | `idle_empty`     | `idle_unrevealed`   | `DeckEmpty` "Reshuffle" button       |
| `DRAW`          | `idle_unrevealed`| `idle_revealed`     | Tap on card, or "Draw" bottom button |
| `DISCARD`       | `idle_revealed`  | `discarding`        | Swipe-down on card, or "Discard"     |
| `DEAL_NEXT`     | `discarding`     | `idle_unrevealed`   | Internal: animation completes        |
| `DECK_EXHAUSTED`| `discarding`     | `idle_empty`        | Internal: deck has no more cards     |

## Invariants

- `tap` on a face-up card is a **no-op**.
- `DISCARD` is only honored while `revealed === true`; it is ignored during
  the `discarding` animation and while the deck is empty.
- The `discarding` state always resolves to either `idle_unrevealed` or
  `idle_empty`; it never returns to `idle_revealed` directly.
