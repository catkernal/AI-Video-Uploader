import os
import json
import random
import glob

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")

NUM_SHOTS = 6  # Generate 6 distinct clips to fill 20 seconds without freeze frames

def load_configs():
    with open(os.path.join(CONFIG_DIR, "animals.json")) as f:
        animals_data = json.load(f)["animals"]
    with open(os.path.join(CONFIG_DIR, "scenes_and_moves.json")) as f:
        scenes_data = json.load(f)
    with open(os.path.join(CONFIG_DIR, "templates.json")) as f:
        templates_data = json.load(f)

    credits_file = os.path.join(CONFIG_DIR, "music_credits.json")
    if os.path.exists(credits_file):
        with open(credits_file) as f:
            credits_data = json.load(f)
    else:
        credits_data = {}

    return animals_data, scenes_data, templates_data, credits_data


def format_character_list(characters):
    """
    Formats the character list into natural English descriptions and short title names.
    """
    n = len(characters)
    desc_items = [
        f"{c['name']} the {c['type']} ({c['color']}, wearing {c['accessory']})"
        for c in characters
    ]
    if n == 1:
        full_desc = desc_items[0]
        title_names = f"{characters[0]['name']} the {characters[0]['type']}"
        verb = "executes"
    elif n == 2:
        full_desc = f"{desc_items[0]} and {desc_items[1]}"
        title_names = f"{characters[0]['name']} & {characters[1]['name']}"
        verb = "execute"
    else:
        full_desc = ", ".join(desc_items[:-1]) + f", and {desc_items[-1]}"
        names_only = [c['name'] for c in characters]
        title_names = ", ".join(names_only[:-1]) + f" & {names_only[-1]}"
        verb = "execute"

    return full_desc, title_names, verb


def _pick_diverse_moves(dance_moves_dict, count):
    """
    Pick *count* moves ensuring body-part diversity.

    dance_moves_dict is keyed by body-part category
    (hands_and_arms, legs_and_feet, hips_and_torso, head_and_face, full_body).
    We cycle through categories so consecutive shots use *different* body parts.
    """
    categories = list(dance_moves_dict.keys())
    random.shuffle(categories)

    picked = []
    cat_idx = 0
    used = set()

    while len(picked) < count:
        cat = categories[cat_idx % len(categories)]
        pool = [m for m in dance_moves_dict[cat] if m not in used]
        if not pool:
            pool = dance_moves_dict[cat]          # allow repeats from this cat
        move = random.choice(pool)
        used.add(move)
        picked.append((cat, move))
        cat_idx += 1

    return picked


def build_next_short_spec(num_animals=None, specific_animals=None):
    """
    Build the full specification for the next short video.

    Returns a dict containing characters, scene, music, prompt, 6-shot plan, etc.
    """
    animals_pool, scenes_info, templates, credits_db = load_configs()

    # --- Character selection (respects --count) ---
    if num_animals is None:
        num_animals = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]

    if specific_animals:
        selected_chars = [a for a in animals_pool if a["type"] in specific_animals]
    else:
        selected_chars = random.sample(animals_pool, min(num_animals, len(animals_pool)))

    chars_desc, title_names, verb = format_character_list(selected_chars)

    scene = random.choice(scenes_info["scenes"])
    weather = random.choice(scenes_info["weathers"])

    # --- Music ---
    available_music = (
        glob.glob(os.path.join(MUSIC_DIR, "*_20s.mp3"))
        + glob.glob(os.path.join(MUSIC_DIR, "*.wav"))
    )
    selected_music = random.choice(available_music) if available_music else None

    music_rel_path = (
        os.path.relpath(selected_music, os.path.join(CONFIG_DIR, ".."))
        if selected_music else ""
    )
    music_info = credits_db.get(music_rel_path) or credits_db.get(selected_music, {})
    attribution_text = music_info.get(
        "attribution_text", "🎵 Music: Royalty-Free Children's Music"
    )

    # --- Build 6-shot choreography plan with diverse body-part moves ---
    dance_moves_dict = scenes_info["dance_moves"]  # now a dict keyed by body part
    shots_list = scenes_info["shots"]

    diverse_moves = _pick_diverse_moves(dance_moves_dict, NUM_SHOTS)
    shots_sample = [random.choice(shots_list) for _ in range(NUM_SHOTS)]

    # Pick the first move as the "primary" for the caption
    primary_body_part, primary_dance_move = diverse_moves[0]

    shots_plan = []
    for idx, ((body_part, move), shot) in enumerate(
        zip(diverse_moves, shots_sample), start=1
    ):
        body_label = body_part.replace("_", " ").title()
        prompt = templates["prompt_template"].format(
            characters_description=chars_desc,
            performance_verb=verb,
            scene=scene,
            weather=weather,
            shot=shot,
            dance_move=move,
        )
        shots_plan.append({
            "index": idx,
            "body_part": body_label,
            "shot": shot,
            "dance_move": move,
            "prompt": prompt,
        })

    # Primary prompt (used for titles / captions / single-shot fallback)
    primary_prompt = templates["prompt_template"].format(
        characters_description=chars_desc,
        performance_verb=verb,
        scene=scene,
        weather=weather,
        shot=shots_sample[0],
        dance_move=primary_dance_move,
    )

    title = templates["title_template"].format(characters_names=title_names)

    base_caption = templates["caption_template"].format(
        characters_names=title_names,
        dance_move=primary_dance_move,
    )
    full_caption = f"{base_caption}\n\n---\n{attribution_text}"

    return {
        "characters": selected_chars,
        "num_characters": len(selected_chars),
        "characters_names": title_names,
        "scene": scene,
        "weather": weather,
        "dance_move": primary_dance_move,
        "prompt": primary_prompt,
        "shots_plan": shots_plan,
        "title": title,
        "caption": full_caption,
        "music_path": selected_music,
        "music_credit": music_info,
    }


if __name__ == "__main__":
    spec = build_next_short_spec()
    print("--- SAMPLE SPECIFICATION ---")
    print(f"Title: {spec['title']}")
    print(f"Cast ({spec['num_characters']}): {spec['characters_names']}")
    print(f"Music: {os.path.basename(spec['music_path'])}")
    print(f"\n6-Shot Choreography Plan:")
    for s in spec["shots_plan"]:
        print(f"  Shot {s['index']}  [{s['body_part']}]  {s['dance_move'][:60]}...")
    print(f"\nCaption:\n{spec['caption']}")
