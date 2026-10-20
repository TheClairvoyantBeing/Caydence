"""
Scriptwriter Engine for Caydence 50+ Minute Reddit / Social Confession One-Shots.
Uses NVIDIA Hosted LLM (Llama 3.2 / Nemotron) to craft long-form, highly engaging narratives.
"""

import os
import re
import sys
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class ScriptwriterEngine:
    """Generates 5-chapter, retention-optimized long-form stories (>8,500 words)."""

    TYPE_1_CHAPTERS = [
        {
            "num": 1,
            "name": "The Cold Open & The Breaking Point",
            "focus": "0:00-0:30 Cold-Open hook in media res, the discovery of betrayal, icy composure, silent exit."
        },
        {
            "num": 2,
            "name": "The Empty Altar & The Locked Doors",
            "focus": "Chaos at the venue, antagonists' entitlement and mockery turning into dread when assets are locked."
        },
        {
            "num": 3,
            "name": "The Midpoint Anchor & The Audit",
            "focus": "Mid-roll retention anchor, forensic paper trail, uncovering financial and relational duplicity."
        },
        {
            "num": 4,
            "name": "The Desperate Confrontation",
            "focus": "Antagonists corner protagonist, arrogance crumples, legal and social consequences materialize."
        },
        {
            "num": 5,
            "name": "The Total Reckoning & Sovereign Horizon",
            "focus": "Cathartic resolution, legal/financial victory, rebuilding a thriving independent life."
        }
    ]

    TYPE_2_CHAPTERS = [
        {
            "num": 1,
            "name": "The Cheap Lease & The Five Rules",
            "focus": "Grounded hook in media res, financial desperation, moving in or taking the post, receiving the bizarre list of mandatory survival rules from the superintendent/predecessor."
        },
        {
            "num": 2,
            "name": "The First Anomaly & The Routine",
            "focus": "Establishing the ordinary daytime routine versus nighttime dread; observing the first breach of reality; strictly following rules under mounting tension."
        },
        {
            "num": 3,
            "name": "The Missing Predecessor & The Broken Protocol",
            "focus": "Investigating past tenants or caretakers who vanished; discovering hidden logs or physical evidence; a rule is nearly broken; the dread becomes visceral and physical."
        },
        {
            "num": 4,
            "name": "The Midnight Event & The Desperate Descent",
            "focus": "The catastrophic climax: alarms sound, anomalous breach occurs, physical rules are executed under sheer survival terror; the elevator, corridor, or boundary collapse."
        },
        {
            "num": 5,
            "name": "The Silence After & The Unending Protocol",
            "focus": "The chilling morning aftermath; emergency services finding nothing; bureaucratic cover-up; living with the haunting truth that you can never let your guard down."
        }
    ]

    TYPE_3_CHAPTERS = [
        {
            "num": 1,
            "name": "Archival Intake & Field Incident Dispatch",
            "focus": "Restricted archival recording header, case background, initial emergency dispatch to the anomalous site, field team assembling equipment."
        },
        {
            "num": 2,
            "name": "Physical Survey & Witness Inquest",
            "focus": "DUA agents conduct forensic interviews with eyewitnesses and deputies; anomalous physical and acoustic measurements taken; initial mapping of discrepancies."
        },
        {
            "num": 3,
            "name": "The Subterranean Breach & Acoustic Log",
            "focus": "Breaching the unrecorded space, vertical shaft, or vault; real-time audio log of field team descending; encountering impossible geometry and audio frequency phenomena."
        },
        {
            "num": 4,
            "name": "Containment Failure & Emergency Protocol",
            "focus": "Containment fails or physical locks release; intense tactical survival in darkness; executing emergency acoustic lockdown codes; radio static and anomalous dread."
        },
        {
            "num": 5,
            "name": "Declassification Disposition & Vault Seal",
            "focus": "Classifying the anomaly; sealing the perimeter with concrete, lead, or demolition; filing the master audio log in sub-basement vaults; lingering dread."
        }
    ]

    def __init__(self, api_key=None, model=None, logger=None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("[ERROR] No NVIDIA_API_KEY configured. Please check your .env file.")
        if OpenAI is None:
            raise ImportError("[ERROR] The 'openai' package is required. Install via pip install openai.")

        self.model = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            timeout=300.0
        )
        self.log = logger or print

    def get_chapter_spec(self, story_type: str = None) -> list:
        stype = str(story_type or "").lower()
        if "2" in stype:
            return self.TYPE_2_CHAPTERS
        if "3" in stype:
            return self.TYPE_3_CHAPTERS
        return self.TYPE_1_CHAPTERS

    def generate_full_story(self, sid: int, sinfo: dict) -> str:
        """Generates all 5 chapters sequentially, enforcing word length standards (50+ min)."""
        title = sinfo["title"]
        hook = sinfo["hook"]
        stype = sinfo.get("type", "Type 1")
        chapters = self.get_chapter_spec(stype)

        self.log(f"--- GENERATING [{stype}] STORY #{sid}: '{title}' ---")

        full_text_parts = []
        accumulated_summary = ""

        for chap in chapters:
            c_num = chap["num"]
            c_name = chap["name"]
            c_focus = chap["focus"]

            self.log(f"  Generating Chapter {c_num}/5: {c_name}...")
            c_text = self._generate_chapter(title, hook, c_num, c_name, c_focus, accumulated_summary, stype=stype)
            words = len(c_text.split())
            self.log(f"    Chapter {c_num} initial draft: {words} words.")

            # Target 1,750+ words per chapter to ensure 8,500+ total words (>50 minutes audio)
            if words < 1700:
                c_text = self._extend_chapter(title, c_num, c_name, c_text, stype=stype)
                words = len(c_text.split())
                self.log(f"    Chapter {c_num} extended to: {words} words.")

            full_text_parts.append(f"Chapter {c_num}: {c_name}\n\n{c_text}")
            accumulated_summary += f"\nChapter {c_num} summary: {c_text[:300]}...\n"
            time.sleep(1)

        full_story = "\n\n".join(full_text_parts)
        return full_story

    def _generate_chapter(self, title, hook, chap_num, chap_name, chap_focus, context, stype="Type 1"):
        if "2" in str(stype):
            system_prompt = (
                "You are a master horror storyteller specializing in 50+ minute viral, high-retention survival-rules and situational protocol audio fiction for Spotify and YouTube. "
                "Your writing is grounded, deeply atmospheric, gritty, and psychologically chilling. Zero sci-fi, no spaceships, no aliens. Everything is grounded in analog realism, quiet dread, and visceral human tension. "
                "Write ONLY the narrative story text for spoken audio. Spoken dialogue must be in natural quotation marks. Do not include markdown headers, stage directions, host greetings, or channel intros."
            )
        elif "3" in str(stype):
            system_prompt = (
                "You are an investigative archival fiction writer specializing in 50+ minute multi-part anomalous organizational case files (inspired by institutional analog horror and declassified audio dossiers for Spotify and YouTube). "
                "Your writing is clinical yet terrifying, grounded in 20th-century bureaucracy, magnetic tape transcripts, forensic inquests, and corporate cover-ups. Zero sci-fi lasers or aliens. "
                "Write ONLY the narrative text for spoken audio. Spoken dialogue must be in natural quotation marks. Do not include markdown headers, stage directions, host greetings, or channel intros."
            )
        else:
            system_prompt = (
                "You are a master long-form YouTube and Reddit storyteller specializing in 50+ minute viral, high-retention audio narratives. "
                "Your writing is deeply immersive, realistic, rich with internal dialogue, atmospheric prose, sensory details, and natural conversational caydence. "
                "Write ONLY the narrative story text for spoken audio. Do not include markdown headers, stage directions, host greetings, or channel intros."
            )

        user_prompt = f"""Story Title: {title}
Core Hook: {hook}
Target Chapter: Chapter {chap_num} of 5 - '{chap_name}'
Chapter Narrative Focus: {chap_focus}

Previous Narrative Context:
{context if context else 'This is the opening of the story.'}

Instructions:
1. Write Chapter {chap_num} in depth, aiming for 1,750 to 2,000 words.
2. Develop the scene beat-by-beat: explore the character's internal thoughts, physical sensations, sensory details, realistic dialogue exchanges, and escalating dramatic tension.
3. Keep the pacing deliberate, immersive, and atmospheric.
4. Output ONLY the story text, formatted in clean narrative paragraphs separated by blank lines."""

        for attempt in range(1, 4):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.75,
                    max_tokens=4096,
                    stream=True
                )
                chunks = []
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        chunks.append(delta)
                    if chunk.choices[0].finish_reason:
                        break
                raw = "".join(chunks).strip()
                clean = self._clean_text(raw)
                return clean
            except Exception as e:
                self.log(f"    [WARN] Generation Chapter {chap_num} attempt {attempt} failed: {e}. Retrying in 5s...")
                time.sleep(5)

        return f"Chapter {chap_num} could not be generated due to API errors."

    def _extend_chapter(self, title, chap_num, chap_name, current_text, stype="Type 1"):
        if "2" in str(stype):
            system_prompt = (
                "You are a master horror story editor and novelist. Your task is to seamlessly expand an existing horror chapter to deepen atmospheric dread, sensory tension, physical details, and grounded psychological terror without rushing."
            )
            extra_instructions = (
                "- Expand sensory details: the sounds, lighting, cold drafts, silence, subtle vibrations, and visceral terror.\n"
                "- Deepen the protagonist's calculating inner voice as they desperately execute the survival rules.\n"
                "- Flesh out conversations and emotional reactions with natural spoken dialogue in quotes."
            )
        elif "3" in str(stype):
            system_prompt = (
                "You are an archival investigative fiction editor. Your task is to seamlessly expand an existing case file chapter to deepen forensic immersion, tape recorder artifacts, investigative procedures, and bureaucratic dread."
            )
            extra_instructions = (
                "- Expand forensic details: technical readouts, reel-to-reel acoustic anomalies, architectural measurements.\n"
                "- Deepen agent dialogue and witness inquest exchanges with natural spoken dialogue in quotes.\n"
                "- Heighten institutional tension and procedural realism."
            )
        else:
            system_prompt = (
                "You are a master story editor and novelist. Your task is to seamlessly expand an existing narrative chapter to add deep character introspection, sensory nuance, dialogue depth, and dramatic tension without rushing."
            )
            extra_instructions = (
                "- Expand sensory details: the textures, scents, lighting, subtle shifts in tone and expression.\n"
                "- Deepen the forensic/financial details and the protagonist's calculating inner voice.\n"
                "- Flesh out conversations and emotional reactions."
            )

        user_prompt = f"""Story Title: {title}
Chapter {chap_num}: {chap_name}
Current Draft:
{current_text}

Task:
The current draft is too short for our 50+ minute audio standard. Rewrite and significantly expand Chapter {chap_num} so that it reaches 1,800 to 2,200 words.
{extra_instructions}
- Do NOT add summaries, intros, or meta-comments. Output ONLY the fully expanded story text."""

        for attempt in range(1, 4):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.75,
                    max_tokens=4096,
                    stream=True
                )
                chunks = []
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        chunks.append(delta)
                    if chunk.choices[0].finish_reason:
                        break
                raw = "".join(chunks).strip()
                clean = self._clean_text(raw)
                if len(clean.split()) > len(current_text.split()):
                    return clean
                return current_text
            except Exception as e:
                self.log(f"    [WARN] Expansion Chapter {chap_num} attempt {attempt} failed: {e}. Retrying...")
                time.sleep(5)

        return current_text

    def generate_drama_script(self, sid: int, sinfo: dict) -> str:
        """Generates multi-character audio drama script with dialogue directions and SFX cues (Type 2)."""
        title = sinfo["title"]
        hook = sinfo["hook"]
        self.log(f"--- GENERATING AUDIO DRAMA SCRIPT FOR STORY #{sid}: '{title}' ---")

        system_prompt = (
            "You are an award-winning cinematic audio drama showrunner and screenwriter. "
            "You write scripts formatted for multi-actor spatial audio production. "
            "Format every spoken line as: CHARACTER (direction): Dialogue line.\n"
            "Format sound effects on separate lines as: [SFX: SFX_NAME].\n"
            "Available sound tags: [SFX: DOOR_SLAM], [SFX: GLASS_SHATTER], [SFX: ROTARY_PHONE_SINGLE_RING], "
            "[SFX: IMPACT_METAL_HEAVY], [SFX: AMBIENCE_START], [SFX: ELEVATOR_CREAK], [SFX: HEARTBEAT_FAST].\n"
            "Format overlapping dialogue blocks with [OVERLAP: START] and [OVERLAP: END].\n"
            "Do NOT include stage directions outside parentheticals or markdown metadata headers."
        )

        user_prompt = f"""Story Title: {title}
Premise/Hook: {hook}

Write an intense, cinematic, high-stakes audio drama scene (1,200 to 2,000 words).
Ensure at least 3 distinct characters engage in sharp, realistic dialogue.
Include dynamic sound cues [SFX: ...] at moments of tension and physical action."""

        for attempt in range(1, 4):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )
                raw = resp.choices[0].message.content.strip()
                clean = self._clean_text(raw)
                if len(clean.split()) >= 300:
                    return clean
            except Exception as e:
                self.log(f"    [WARN] Audio drama script generation attempt {attempt} failed: {e}. Retrying in 3s...")
                time.sleep(3)

        # Fallback scripted dramatic template if LLM is unavailable
        return f"""# {title}

MAYA (tense whisper)
Arthur, look at the terminal right now. The encryption key just invalidated itself.

[SFX: ROTARY_PHONE_SINGLE_RING]

ARTHUR (gravelly, steady)
Keep your hand off the receiver, Maya. We are not scheduled for an inbound line at this hour.

DAVID (calling from down the corridor)
Hey! The blast door on sub-level four just sealed itself. The hydraulics fired without manual override!

[SFX: IMPACT_METAL_HEAVY]

ARTHUR (urgent)
Get inside the security cage, David!

[OVERLAP: START]
DAVID (panicked)
The gate won't move! The interlock is dead!
MAYA (shouting)
Pull the manual release lever behind the conduit!
[OVERLAP: END]

[SFX: ELEVATOR_CREAK]

CLAIRE (calm, icy over intercom)
Good evening, gentlemen. You should not have unsealed the 1994 archive.

ARTHUR (defiant)
Claire, the board revoked your sovereign signatory authority two hours ago. Every bank wire you routed is frozen.

[SFX: GLASS_SHATTER]

MAYA (rapid)
Arthur, she cut the main grid feed. We're on emergency battery reserve. We have six minutes before ventilation halts.

ARTHUR (determined)
Six minutes is five minutes more than we need. Hand me the master bypass key.
"""

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r'^(?:Here is|Sure,|Certainly).+?\n\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\n(?:I hope you enjoy|Let me know if).+?$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^#+ .+$', '', text, flags=re.MULTILINE)
        return text.strip()
