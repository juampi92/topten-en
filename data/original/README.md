# Data/original

This folder contains the Python scripts used to process the original game. The output of this was `cards_es.json`.

I will leave these scripts here as educational material, but the translation was already performed, so we don't have to do it again.

Steps:

1. `extract_cards.py` will read a file (for example `/game_cards/1_A.jpeg`), call the prompt, and put the output in `/game_cards_data/` using the same name as the input but with json.
    - The prompt (structured response) and the output use the same structure, in `schema.json`.
    - The most useful thing might be the prompt and the structure.
    - Compressing the image produced bad results, but it was cheaper.

2. `audit.py` will:
    - Make sure the card prompts are not empty (it happened with low quality).
    - Make sure all card prompts have a `<green></green>` and `<red></red>` tags. (cheaper models failed to always extract the right colors).
    - If there are some missing, it will show it, so I would manually add them. I had to do this with 10-15 of them approximately.

3. `merge.py` will take all of the `.json` and combine them.
    - It will take a coordinate (col: x, row: y) and grab the top and bottom prompts from `_A` and the same for `_B`, and combine them into one `card` object.

4. Continue to the [translation section](../translation/README.md).