import json
import os

HISTORY_DIR = "public/history"
INDEX_FILE = os.path.join(HISTORY_DIR, "index.json")

# Diese Saisons sollen aus dem Dropdown verschwinden - die zugehörigen
# JSON-Dateien bleiben aber auf der Festplatte liegen (z.B. für später
# geplante Legacy-Badges).
SEASONS_TO_HIDE = {"2021", "2022", "2023", "2024", "2025"}

with open(INDEX_FILE, encoding="utf-8") as f:
    history_index = json.load(f)

before = len(history_index)
history_index = [e for e in history_index if e["season"] not in SEASONS_TO_HIDE]
after = len(history_index)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(history_index, f, indent=2, ensure_ascii=False)

print(f"{before - after} Einträge aus dem Dropdown entfernt ({before} -> {after}).")
print("Die zugehörigen JSON-Dateien in public/history/ bleiben unverändert erhalten.")
