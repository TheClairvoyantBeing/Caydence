# Voice Reference Audio Licensing & Attribution

This document logs the licensing, provenance, and rights status for all reference audio clips used within Caydence voice cloning and TTS benchmarking pipelines.

---

## 1. Zero-Shot TTS Watermarking
- **Engine:** Chatterbox-TTS (MIT License)
- **Watermark Policy:** In accordance with ethical AI deployment standards and commercial safety requirements, the Perth watermarker is **enabled** by default on all generated clone waveforms.
- **Disclosure:** AI-generated audio is marked and disclosed in production metadata.

---

## 2. Voice References

### Arthur Vance (`narrator_22k.wav`)
- **Archetype:** Grounded Baritone / Senior Archivist
- **Source:** CC0 Public Domain Speech Corpus / Open Voice Archive
- **License:** Creative Commons Zero (CC0 1.0 Universal)
- **Usage Rights:** Commercial and non-commercial reproduction, modification, and distribution permitted without attribution.

### Procedural & Neural Voice Providers
- **Microsoft Neural Voices (edge-tts):** Used for non-commercial research, prototyping, and pilot demonstration.
- **Kokoro-82M:** Apache 2.0 open-weights model.
- **Dia Multi-Speaker:** Apache 2.0 dialogue framework.
- **Azure Speech HD / ElevenLabs:** Supported via plug-in interface when API credentials are provided by the user.

---

## 3. Foley & SFX Licensing Policy
- **Freesound API Imports:** Strictly filtered to `license:"Creative Commons 0"` (CC0).
- **Procedural Foley Waveforms:** Synthesized via NumPy/SciPy physical modeling algorithms in float32; entirely public domain and unencumbered.
