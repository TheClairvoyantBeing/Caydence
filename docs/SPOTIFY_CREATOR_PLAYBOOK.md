# Spotify for Creators: Comprehensive Production & Growth Playbook

A definitive reference guide synthesized from official Spotify for Creators documentation, specifications, show art standards, and audience growth strategies.

---

## 1. Executive Overview

Spotify offers two distinct creator platforms:
- **Spotify for Creators** (formerly Anchor): The hosting, publishing, analytics, and video podcast platform for audio dramas, serialized fiction, talk shows, and video podcasts.
- **Spotify for Artists**: The music distribution hub requiring third-party distributor delivery (e.g., DistroKid, TuneCore, CD Baby) to manage musician profiles and royalties.

For audio dramas, narrations, and podcast series produced by **Caydence**, all publishing and audience development is managed through **Spotify for Creators**.

---

## 2. Audio Episode Standards & Upload Guidelines

### 2.1 Technical Audio Specifications
| Parameter | Spotify Specification | Caydence Production Standard |
| :--- | :--- | :--- |
| **Supported Formats** | MP3, WAV, M4A | **256 kbps CBR MP3** & **48 kHz float32 WAV** |
| **Channel Layout** | Stereo or Mono | **Stereo (2-Channel)** |
| **Sample Rate** | 44.1 kHz or 48 kHz | **48.0 kHz** (Broadcast Standard) |
| **Bitrate (MP3)** | 128 kbps to 320 kbps | **256 kbps CBR** (Optimal balance of quality & streamability) |
| **Loudness Target** | ITU-R BS.1770 / EBU R128 | **-16.0 LUFS Integrated (±0.5 LUFS)** |
| **True-Peak Ceiling** | -1.0 dBFS / dBTP | **-1.0 dBTP** (Prevents inter-sample clipping on lossy transcode) |
| **File Size Limit** | No hard limit | Recommended < 250 MB for reliability |

> [!IMPORTANT]
> **Metadata & ID3 Tag Optimization**: Keep embedded ID3v2 tags and embedded cover images inside MP3 files as small as possible. Bloated ID3 headers can cause processing timeouts and upload errors during mobile or web intake.

### 2.2 Episode Publishing Workflow
1. **Upload**: Upload via Spotify for Creators Web (`New episode` > `Select a file`).
2. **Details Page**:
   - **Title**: Clear, keyword-rich, episode-specific title (e.g., `Case 401: The Blackwood Sinkhole`).
   - **Description**: Engaging synopsis, chapter markers, character voices, and relevant tags.
   - **Season & Episode Numbers**: Always specify (e.g., Season 1, Episode 1) to enable sequential chronological listening for narrative dramas.
   - **Episode Artwork**: Custom thumbnail matching the episode's subject.
   - **Content Checks**: Mark Clean or Explicit accurately.
3. **Publishing Options**:
   - **Publish Now**: Instant live release.
   - **Schedule**: Schedule release date/time in local timezone.
   - **Revert to Draft**: Available via episode menu (3 dots) before or after scheduling.

---

## 3. Video Podcasting Specifications

Video podcasts significantly boost organic discoverability on Spotify (time spent with video content on Spotify more than doubled year-over-year).

### 3.1 Technical Video Specifications
| Feature | Spotify Requirement | Recommendation |
| :--- | :--- | :--- |
| **Container Formats** | MP4, MOV, MPG | **MP4** |
| **Video Codec** | H.264 High Profile | H.264 High Profile |
| **Aspect Ratio** | 16:9 Widescreen | 1920x1080 (1080p) or 3840x2160 (4K) |
| **Max Bitrate** | 25 Mbps (1080p) / 35 Mbps (4K) | 12–16 Mbps (1080p) |
| **Frame Rate** | Native source frame rate | 24 fps, 25 fps, or 30 fps |
| **Tracks** | Exactly 1 video track + 1 audio track | Avoid multi-audio/subtitle track multiplexing |
| **Max Duration** | 12 hours | Ideal episode length: 30–80 min |
| **Audio Codec** | AAC-LC, Stereo, 192 kbps or higher | AAC-LC @ 256 kbps, 48 kHz Stereo |

### 3.2 Dual Distribution Dynamics
- Video episodes are hosted on Spotify and stream natively with video on desktop, mobile, and TV apps.
- For external podcast platforms (Apple Podcasts, Overcast, etc.) connected via RSS, Spotify automatically extracts and serves the audio track seamlessly.
- You can replace an existing audio-only episode with a video episode later without losing stats or comments.

---

## 4. Show Art & Thumbnail Design: The Complete Guide

Show artwork is the primary visual storefront for your show across Spotify's mobile feeds, search results, car displays, and TV interfaces.

### 4.1 Master Image Dimensions & Format
- **Aspect Ratio**: Exact `1:1` Square.
- **Recommended Dimensions**: **3000 × 3000 pixels**.
- **Minimum Dimensions**: **1400 × 1400 pixels**.
- **File Format**: **JPEG (.jpg)** or **PNG (.png)**.
- **Color Space**: **sRGB / RGB** (Never CMYK; CMYK will cause color distortion on digital displays).

### 4.2 The "Do's and Don'ts" Design Rules
```
DO:
  ✓ Use high-resolution, sharp visual assets (3000 x 3000 px).
  ✓ Test at tiny sizes: design must be readable at 50 x 50 px thumbnail scale.
  ✓ Use simple, bold, high-contrast imagery with solid backgrounds or subtle gradients.
  ✓ Limit typography to maximum 2 complementary fonts (e.g., serif title + clean sans-serif subtext).
  ✓ Feature your show logo/title prominently as the primary visual anchor.
  ✓ Leverage color psychology:
      - Dark teal / navy / cold grey: Mystery, archival intrigue, noir thriller.
      - Deep amber / crimson: Tension, warning, supernatural danger.
      - Contrast opposites (complementary colors) to make elements pop off dark themes.

DON'T:
  ✗ DO NOT stretch or upscale low-resolution images.
  ✗ DO NOT clutter the canvas with excessive text, credits, URLs, or episode numbers.
  ✗ DO NOT include the word "Podcast" in the title art (it is redundant and wastes space).
  ✗ DO NOT mix multiple competing patterns, illustrations, and busy photo collages together.
  ✗ DO NOT place critical lettering near the very edge (maintain a 10% safety margin).
```

### 4.3 Logo vs. Cover Art
- **Show Logo**: A clean, isolated brand mark (title lettering + icon) that can be reused on social banners, merch, and press kits.
- **Cover Art**: The complete square canvas incorporating the logo, background texture, character/thematic illustration, and atmospheric grading.

---

## 5. Discoverability & Audience Growth Playbook

### 5.1 Spotify-Native Growth Features
1. **Vertical Clips (Spotify's #1 Organic Discovery Tool)**:
   - **Format**: `9:16` Vertical Video, **90 seconds or less**.
   - **Limit**: 1 clip per episode.
   - **Placement**: Featured algorithmically on Spotify's Home Feed, Podcasts Feed, Browse Tab, and "Now Playing" drawer.
   - **Selection Rule**: "Give the gold away" — pick the most gripping 45–60s climax, plot revelation, or dialogue twist. Never use generic tease/clickbait.
2. **Show Page Curation**:
   - **"Best Place to Start" Episode**: Pin your strongest introductory episode (e.g., *Case 401* or *The Wheeler Highrise Protocol*) so new listeners are not overwhelmed.
   - **Host Recommendations**: Pin up to 2 external Spotify recommendations (music album, playlist, or related show) to personalize the creator profile.
   - **Custom Episode Artwork**: Upload a distinct thumbnail for every single episode to increase click-through rate in search results.
3. **Transcripts, Chapters & Topic Tags**:
   - Spotify automatically generates interactive transcripts for every published episode.
   - Transcripts power backend keyword search indexing, topic tags, and chapter markers.
   - Pronounce key character names, locations, and episode concepts clearly to ensure accurate search indexing.

### 5.2 SEO & Answer Engine Optimization (AEO)
- **Traditional SEO**:
  - Title structure: `[Show Name / Series] - [Episode Title / Case Number]`.
  - Include high-intent search terms in the first 2 lines of the description (e.g., *horror audio drama*, *weird fiction*, *creepypasta*, *found footage podcast*).
- **AEO (AI Search & Answer Engines - ChatGPT, Perplexity, Claude)**:
  - AI engines pull from structured metadata, transcripts, and show notes.
  - Write concise 2–3 sentence factual summaries answering *Who, What, Where, and What Genre*.
  - Maintain structured episode notes with clear headings (Premise, Characters, Case Timeline).

### 5.3 Fan Retention & Community Interaction
- **Polls in Episodes**:
  - Insert interactive polls directly into episodes via Spotify for Creators.
  - Solicit audience votes on character decisions, theory confirmations, or preferred genres for upcoming episodes.
- **Episode Q&A and Comments**:
  - Reply to early listener comments within the first 24 hours of release.
  - Active comment threads signal high engagement to the recommendation algorithm.
- **Owned Audience Channels**:
  - Direct listeners to an email newsletter or dedicated webpage for extended case files, archival lore, and early production updates.

---

## 6. Music Distribution Reference (For Soundtrack / OST Releases)

If publishing standalone musical scores, OST albums, or ambient stem tracks related to Caydence shows:
1. Cannot be uploaded directly via Spotify for Creators (which is podcast/spoken-word only).
2. Must be delivered via an approved Spotify distributor:
   - **Preferred Distributors**: DistroKid, CD Baby, TuneCore, Symphonic, EmuBands.
3. Once distributed, claim the artist profile on **Spotify for Artists** (`artists.spotify.com`) for canvas videos, artist pick playlists, and release radar pitching.

---

## 7. Caydence Audio Drama Checklist

Before publishing any new episode to Spotify:
- [ ] **Audio Master**: 48 kHz Stereo WAV and 256 kbps CBR MP3 rendered.
- [ ] **Loudness**: Verified at `-16.0 LUFS` with true-peak at `-1.0 dBTP`.
- [ ] **Artwork**: 3000 × 3000 px sRGB JPEG, legible at mobile thumbnail size, no "Podcast" wording.
- [ ] **Metadata**: Season number, episode number, case title, full character cast credited.
- [ ] **Description**: 2-sentence hook, synopsis, lore notes, search tags.
- [ ] **Discovery Clip**: 30–60s vertical 9:16 video clip prepared for Spotify feed discovery.
- [ ] **Interactive**: 1 poll or discussion question attached to the episode.
