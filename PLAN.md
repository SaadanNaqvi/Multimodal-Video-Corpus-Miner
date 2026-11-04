
Build plan:
- Ingest:

Take a manifest of videos, read metadata with ffprobe, hash the content, and quarantine corrupt files. Use a properly licensed dataset or Creative Commons videos, not scraped YouTube.

- Decode and Segment:

Use ffmpeg to extract 16 kHz mono audio and sample frames, then split videos into shots with PySceneDetect.

- Extract Features:

Speech: timestamped transcripts from faster-whisper
Visuals: CLIP embeddings from open_clip
Audio: spectrogram features or CLAP embeddings

- Alighn on one timeline:

Turn shots, words, and audio into a single segment record, with explicit handling for missing modalities and variable frame rates. This is the core multimodal problem, so give it the most care.

- Store and Query:

Write Parquet shards with a versioned schema and query them with DuckDB. Add a vector index such as FAISS for searches like "find clips showing X where someone says Y."

- Mine and Filter:

Remove near-duplicates with perceptual hashes, and add quality filters for blur, silence, and low speech confidence.