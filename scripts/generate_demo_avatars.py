"""Deterministic original SVG portraits of fictional demo people; no real photos or remote URLs."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "apps/web/public/demo-avatars/v1"
PALETTES = (
    ("#dceee8", "#e9b28c", "#604637", "#42958c", "bob"),
    ("#e3e9f6", "#dca581", "#283b4c", "#526da4", "short"),
    ("#f4e6de", "#ebba98", "#70462e", "#9b7562", "bob"),
    ("#deecf4", "#c78a65", "#392f2d", "#477caa", "short"),
    ("#eee8f5", "#f0c6a6", "#995b37", "#8c7aab", "long"),
    ("#e5eee0", "#d6a482", "#685046", "#6d9463", "short"),
    ("#e4f0ee", "#a96e4e", "#312c2b", "#458b83", "long"),
    ("#e5e9f0", "#efd0ae", "#856343", "#62788e", "short"),
    ("#f5e9e1", "#d79c73", "#42342f", "#a77765", "bob"),
    ("#e1eef2", "#edb58d", "#3c484d", "#4e879d", "short"),
    ("#eee9de", "#e0ab82", "#6e4f33", "#9b8a5c", "long"),
    ("#e9e5f3", "#bb805d", "#343038", "#7c6b9b", "short"),
)


def portrait(background: str, skin: str, hair: str, shirt: str, style: str) -> str:
    back = '<path d="M15 34V24c0-21 34-21 34 0v24H15Z" fill="' + hair + '"/>' if style == "long" else ""
    top = (
        '<path d="M18 29V23c0-17 29-19 29 2v10l-5-15c-7 6-15 4-20 1Z"/>'
        if style == "short"
        else '<path d="M16 33V24c0-20 33-20 33 0v12l-6-16c-8 6-16 4-20 0l-3 17Z"/>'
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<!-- Original fictional demo illustration; not a portrait of a real BIOCAD employee. -->
<defs><clipPath id="portrait"><circle cx="32" cy="32" r="31"/></clipPath></defs>
<g clip-path="url(#portrait)"><path fill="{background}" d="M0 0h64v64H0z"/>{back}
<path fill="{shirt}" d="M8 65c1-22 47-22 48 0Z"/>
<path fill="{skin}" d="M27 39h10v11c-2 3-8 3-10 0Z"/>
<ellipse fill="{skin}" cx="32" cy="29" rx="14" ry="18"/>
<g fill="{hair}">{top}</g><g fill="#273548"><circle cx="27" cy="30" r="1.15"/>
<circle cx="37" cy="30" r="1.15"/></g><path d="M29 38q3 2 6 0" fill="none"
stroke="#9b6655" stroke-width="1.4" stroke-linecap="round"/>
<path d="M31 32v3h2" fill="none" stroke="#ac795d" stroke-linecap="round" opacity=".5"/>
</g></svg>
"""


def main():
    fixture_path = ROOT / "docs/data/demo_fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for index, person in enumerate(fixture["employees"]):
        (DESTINATION / (person["id"] + ".svg")).write_text(
            portrait(*PALETTES[index % len(PALETTES)]), encoding="utf-8"
        )
        person["avatar_url"] = f"/demo-avatars/v1/{person['id']}.svg"
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(fixture['employees'])} original fictional SVG portraits")


if __name__ == "__main__":
    main()
