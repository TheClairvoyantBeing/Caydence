# Caydence Audio & Story Production Rules

## 1. Numbers in Words Rule (STRICT MANDATE)
All numbers MUST be written out in words across all stories, text files (`story.md`, `story.txt`), and audio synthesis scripts. Spoken narration must NEVER encounter raw numeric digits or unexpanded dates/times.

### Expansion Guide:
* **Dates**: `March 10, 1987` $\rightarrow$ `March tenth, nineteen eighty-seven`
* **Timestamps / Hours**: `14:43:01` $\rightarrow$ `fourteen forty-three oh-one` (or `fourteen forty-three and one second`), `03:00` $\rightarrow$ `three o'clock` (or `zero-three hundred hours`)
* **Case, Unit, and Location Codes**:
  * `Case 401` $\rightarrow$ `Case four hundred one` / `Case four-zero-one`
  * `Unit 401` $\rightarrow$ `Unit four-zero-one`
  * `Room 104` $\rightarrow$ `Room one-zero-four`
  * `Cell 19` $\rightarrow$ `Cell nineteen`
  * `Tower 9` $\rightarrow$ `Tower nine`
  * `Sub-Basement 6` $\rightarrow$ `Sub-Basement six`
* **Measurements & Distances**:
  * `300 feet` $\rightarrow$ `three hundred feet`
  * `1,500 feet` $\rightarrow$ `fifteen hundred feet`
  * `3.7 meters` $\rightarrow$ `three point seven meters`
* **Decades & Ordinals**:
  * `mid-60s` $\rightarrow$ `mid-sixties`
  * `1970s` $\rightarrow$ `nineteen seventies`
  * `10th` $\rightarrow$ `tenth`, `1st` $\rightarrow$ `first`, `22nd` $\rightarrow$ `twenty-second`
  * `30-minute` $\rightarrow$ `thirty-minute`
* **Roman Numerals in Dialogue**:
  * `IV, V, VI` $\rightarrow$ `four, five, six`

---

## 2. Universal File Naming Convention
* Standard format: `T{type}S{season}E{episode}-{StoryTitle}.wav` / `.mp3`
  * Example: `T3S1E1-TheBlackwoodSinkhole.wav`
  * Kokoro model prefix: `Kokoro-T3S1E1-TheBlackwoodSinkhole.wav`
  * Multi-voice Kokoro prefix: `Kokoro-multi-T3S1E1-TheBlackwoodSinkhole.wav`

---

## 3. Broadcast Audio & Loudness Standards
* **Spotify Releases**: High-Bitrate MP3 (**256 kbps CBR, 48 kHz, Stereo**)
* **Archival Masters**: WAV (**48 kHz, 32-bit Float Stereo**)
* **Mastering Standard**: EBU R128 (`-16.0 LUFS integrated`, `-1.0 dBTP true-peak ceiling`)
* **Dialogue Pacing**:
  * `650ms` breathing pause between speaker turns
  * `350ms` punctuation pause between sentences
* **Zero Spoken Script Labels**: Strip speaker cues (`Miller:`, `Vance:`, `Dispatch:`) before TTS synthesis.
