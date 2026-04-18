import os
import sys
import json
import shutil
from server.models.schemas import ScriptData, SeoData
from server.services.state import PROJECT_ROOT


def _ensure_scripts_importable():
    scripts_dir = os.path.join(PROJECT_ROOT, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def generate_script_from_book(video_number: int = 1) -> tuple[ScriptData, SeoData]:
    """Run the full 02_write_script.py flow reading from book."""
    _ensure_scripts_importable()
    old_cwd = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        os.environ["VIDEO_NUMBER"] = str(video_number)

        import importlib
        mod = importlib.import_module("02_write_script")
        importlib.reload(mod)
        mod.main()

        return _load_current_script()
    finally:
        os.chdir(old_cwd)


def generate_script_from_custom(content: str, custom_prompt: str = None, video_number: int = 1) -> tuple[ScriptData, SeoData]:
    """Generate script from user-provided text, optionally with custom prompt."""
    _ensure_scripts_importable()
    old_cwd = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)

        import importlib
        mod = importlib.import_module("02_write_script")
        importlib.reload(mod)

        if custom_prompt:
            full_prompt = f"""{custom_prompt}

Content to work with:
{content}

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "shorts": [
        {{
            "angle_type": "custom",
            "youtube_title": "Title under 60 chars ending with #Shorts",
            "description": "YouTube description with hashtags",
            "hook": "Opening hook line",
            "script": "Main script body (40-70 words)",
            "cta": "Call to action / loop ending",
            "tags": ["shorts", "youtubeshorts", "motivation"],
            "category_id": "27"
        }}
    ]
}}
Only JSON. No extra text."""
            text = mod.ask_gemini(full_prompt)
            script_data = mod.parse_json_safe(text, retries_left=2, prompt=full_prompt)
        else:
            script_data = mod.write_shorts_scripts(content, "custom_input")

        short_idx = min(video_number - 1, len(script_data["shorts"]) - 1)
        my_short = script_data["shorts"][short_idx]

        os.makedirs("output/sections", exist_ok=True)
        with open("output/sections/01_hook.txt", "w", encoding="utf-8") as f:
            f.write(my_short["hook"])
        with open("output/sections/02_script.txt", "w", encoding="utf-8") as f:
            f.write(my_short["script"])
        with open("output/sections/03_cta.txt", "w", encoding="utf-8") as f:
            f.write(my_short["cta"])

        tags = list(mod.CORE_TAGS)
        existing_lower = {t.lower() for t in tags}
        for t in my_short.get("tags", []):
            if t.lower() not in existing_lower:
                tags.append(t)
                existing_lower.add(t.lower())
        tags = mod.sanitize_tags(tags)

        description = my_short.get("description", "")
        if "#Shorts" not in description and "#shorts" not in description:
            description = description.rstrip() + "\n\n" + mod.FALLBACK_HASHTAGS

        seo_data = {
            "youtube_title": my_short["youtube_title"],
            "description": description,
            "tags": tags,
            "keywords": tags,
            "category": "Education",
            "category_id": my_short.get("category_id", "27"),
            "angle_type": my_short.get("angle_type", ""),
        }
        with open("output/seo_data.json", "w", encoding="utf-8") as f:
            json.dump(seo_data, f, indent=2, ensure_ascii=False)

        full_script = f"{my_short['hook']} {my_short['script']} {my_short['cta']}"
        with open("output/latest_script.txt", "w", encoding="utf-8") as f:
            f.write(full_script)

        return _load_current_script()
    finally:
        os.chdir(old_cwd)


def save_script(script: ScriptData, seo_data: SeoData):
    """Save edited script and SEO data back to output files."""
    output_dir = os.path.join(PROJECT_ROOT, "output")
    sections_dir = os.path.join(output_dir, "sections")
    os.makedirs(sections_dir, exist_ok=True)

    with open(os.path.join(sections_dir, "01_hook.txt"), "w", encoding="utf-8") as f:
        f.write(script.hook)
    with open(os.path.join(sections_dir, "02_script.txt"), "w", encoding="utf-8") as f:
        f.write(script.body)
    with open(os.path.join(sections_dir, "03_cta.txt"), "w", encoding="utf-8") as f:
        f.write(script.cta)

    seo_dict = seo_data.model_dump()
    with open(os.path.join(output_dir, "seo_data.json"), "w", encoding="utf-8") as f:
        json.dump(seo_dict, f, indent=2, ensure_ascii=False)

    full_script = f"{script.hook} {script.body} {script.cta}"
    with open(os.path.join(output_dir, "latest_script.txt"), "w", encoding="utf-8") as f:
        f.write(full_script)


def _load_current_script() -> tuple[ScriptData, SeoData]:
    """Load script and SEO data from output files."""
    output_dir = os.path.join(PROJECT_ROOT, "output")
    sections_dir = os.path.join(output_dir, "sections")

    script = ScriptData()
    hook_path = os.path.join(sections_dir, "01_hook.txt")
    body_path = os.path.join(sections_dir, "02_script.txt")
    cta_path = os.path.join(sections_dir, "03_cta.txt")

    if os.path.exists(hook_path):
        script.hook = open(hook_path, "r", encoding="utf-8").read()
    if os.path.exists(body_path):
        script.body = open(body_path, "r", encoding="utf-8").read()
    if os.path.exists(cta_path):
        script.cta = open(cta_path, "r", encoding="utf-8").read()

    seo_data = SeoData()
    seo_path = os.path.join(output_dir, "seo_data.json")
    if os.path.exists(seo_path):
        with open(seo_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        seo_data = SeoData(**data)

    return script, seo_data
