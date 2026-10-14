"""Synthetic bounded-work measurements, not claims about disk-library import throughput."""
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from auravlian.app.bootstrap import create_application
from auravlian.domain.models.track import Track
from auravlian.presentation.widgets.track_table import TrackTableModel, TrackFilterModel
from auravlian.infrastructure.audio.visualizer import spectrum

app = create_application([])
model = TrackTableModel()
model.replace([Track(Path(f"{i}.wav"), f"Track {i}", "Artist", "Album", i * 1000) for i in range(5000)])
proxy = TrackFilterModel()
proxy.setSourceModel(model)
started = perf_counter()
for query in ("4999", "Artist", "absent", "Track 1", ""):
    proxy.search(query)
    proxy.rowCount()
search_ms = (perf_counter() - started) * 1000 / 5
samples = np.sin(2 * np.pi * 440 * np.arange(4096) / 16000)
started = perf_counter()
for _ in range(100):
    spectrum(samples, 16000)
fft_ms = (perf_counter() - started) * 10
result = {"rows": 5000, "mean_search_ms": round(search_ms, 3), "mean_fft_frame_ms": round(fft_ms, 3),
          "spectrum_throttle_ms": 50, "maximum_fft_samples": 4096}
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
