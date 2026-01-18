import json
from pathlib import Path


def _flatten_keys(data: object, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(_flatten_keys(value, full_key))
    return keys


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_translations_cover_all_strings_keys() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    base_path = repo_root / "custom_components" / "ha_artnet_relay" / "strings.json"
    translations_dir = (
        repo_root / "custom_components" / "ha_artnet_relay" / "translations"
    )

    base = _load_json(base_path)
    base_keys = _flatten_keys(base)

    for translation_path in sorted(translations_dir.glob("*.json")):
        translation = _load_json(translation_path)
        translation_keys = _flatten_keys(translation)
        missing = sorted(base_keys - translation_keys)
        extra = sorted(translation_keys - base_keys)
        assert not missing and not extra, (
            f"{translation_path.name} missing keys: {', '.join(missing)}; "
            f"extra keys: {', '.join(extra)}"
        )