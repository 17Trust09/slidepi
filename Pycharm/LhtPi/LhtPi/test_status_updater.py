import json
import time
import itertools

# Beispiel-Dateien zur Simulation
playlist = [
    {"filename": "Bild1.jpg", "duration": 5},
    {"filename": "Bild2.jpg", "duration": 10},
    {"filename": "Video.mp4", "duration": 7}
]

# Endlosschleife mit endlosem Durchlauf durch Playlist
for item in itertools.cycle(playlist):
    filename = item["filename"]
    duration = item["duration"]

    for remaining in range(duration, 0, -1):
        state = {
            "status": "playing",
            "current_media": filename,
            "time_left": remaining
        }

        with open("state.json", "w") as f:
            json.dump(state, f)

        time.sleep(1)

    # Nach dem Ende des Mediums 1 Sekunde "Pause" simulieren
    with open("state.json", "w") as f:
        json.dump({
            "status": "paused",
            "current_media": filename,
            "time_left": 0
        }, f)

    time.sleep(1)
