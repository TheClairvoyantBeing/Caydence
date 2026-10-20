import os
import re
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class StoryEngine:
    """
    Core engine for horror/mystery story generation.
    It utilizes NVIDIA's NIM (hosted Llama-3 / Nemotron models) to produce 
    YouTube-optimized Reddit-style 'nosleep' content with high audience retention.
    """
    # 10 Core Story Video Types & Frameworks
    STORY_TYPES = {
        "personal_storytime": (
            "Personal Storytime: First-person account of an intense, scary, or pivotal life experience "
            "with intimate reactions and lessons learned."
        ),
        "reddit_internet": (
            "Reddit / Internet Stories (One-Shot): Full self-contained story starting and ending in one single episode (50+ min), "
            "featuring authentic internet caydence, high emotional stakes, and sequential [EDIT] updates."
        ),
        "horror_scary": (
            "Horror & Scary Stories (Multi-Series): Multi-part suspenseful narrative (Part 1, Part 2...) "
            "with chilling atmosphere, atmospheric dread, and cliffhanger transitions."
        ),
        "animated": (
            "Animated Story Script: Visual-friendly narrative with dynamic scene descriptions and punchy dialogue."
        ),
        "true_crime": (
            "True Crime & Mystery (Multi-Series): Investigative breakdown of unexplained cases, timelines, evidence, "
            "and trials structured in multi-part series."
        ),
        "history_bio": (
            "History & Biography (Multi-Series): Epic documentary narrative of historical turning points or figures."
        ),
        "documentary": (
            "Documentary / Mini-Doc (Multi-Series): In-depth investigative chapters with timeline reveals."
        ),
        "fiction_dramatized": (
            "Fiction / Dramatized Series (90+ min): Foolproof, multi-character immersive drama "
            "(Mafia, Werewolf/Alpha, Billionaire/Elite Betrayal, Mystery Thriller - NO Sci-Fi)."
        ),
        "mafia_werewolf": (
            "Mafia & Werewolf Fiction (90+ min): High-stakes elite betrayal, syndicate loyalty, or pack alpha dynamics "
            "spanning an epic foolproof narrative."
        ),
        "story_gameplay": (
            "Story-Based Gameplay: Immersive role-play survival or quest adventure."
        ),
        "commentary": (
            "Commentary with a Story: Analytical breakdown of dramatic internet events."
        ),
        # Legacy horror archetypes
        "mr_nightmare": "Grounded Realism / Stalker / Night Encounter (Mr. Nightmare style - Multi-Series)",
        "dark_somnium": "Atmospheric / Paranormal / Rules Horror (The Dark Somnium style - Multi-Series)",
        "creepypasta": "Classic Creepypasta / Cryptid / Urban Legend (Multi-Series)"
    }

    def __init__(self, api_key=None, model=None):
        """
        Connects to the NVIDIA NIM base URL.
        Requires a valid NVIDIA_API_KEY from the NIM dashboard.
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("[ERROR] No NVIDIA_API_KEY found. Check your .env file.")
        
        if OpenAI is None:
            raise ImportError("[ERROR] The 'openai' package is required for StoryEngine. Install it with 'pip install openai'.")
        
        self.model = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )

    def generate_story(self, topic, duration_str, style="horror_scary", multi_voice=False, episode_context=None):
        # Duration standards:
        # Standard: 50+ min (min 8,500 - 10,000 words, matching Output 5 & 6)
        # Fiction / Mafia / Werewolf: 90+ min (min 15,000 - 17,500 words)
        targets = {
            "50": (8500, 10000),
            "50+": (8500, 10500),
            "60": (9500, 11500),
            "90": (15000, 17500),
            "90+": (15000, 18000),
            "custom": (8500, 12000)
        }
        
        # Default minimum duration is 50 min for standard, 90 min for fiction
        if str(duration_str) not in targets:
            if style in ["fiction_dramatized", "mafia_werewolf"]:
                target_range = (15000, 17500)
                duration_str = "90+"
            else:
                target_range = (8500, 10000)
                duration_str = "50+"
        else:
            target_range = targets[str(duration_str)]
            
        min_words, max_words = target_range
        style_desc = self.STORY_TYPES.get(style, self.STORY_TYPES.get("reddit_internet"))

        # Format enforcement based on category
        format_guideline = ""
        if style == "reddit_internet":
            format_guideline = """
FORMAT REQUIREMENT — ONE-SHOT REDDIT STORY:
- This must be a ONE-SHOT story starting and concluding completely within this single episode.
- Follow an authentic Reddit confession / drama / personal dilemma caydence with [UPDATE] and [EDIT] sections.
- Minimum duration: 50+ minutes (~8,500+ words). Complete beginning-to-end satisfaction.
"""
        elif style in ["fiction_dramatized", "mafia_werewolf"]:
            format_guideline = """
FORMAT REQUIREMENT — FOOLPROOF FICTION (90+ MINUTES):
- High-stakes, airtight narrative (Mafia, Werewolf / Alpha pack, Elite Betrayal, Mystery).
- STRICT RULE: ABSOLUTELY NO SCI-FI MOVIES, ALIEN, CYBERPUNK, OR SCI-FI THEMES. Focus on raw human drama, power structures, loyalty, and betrayal.
- Minimum duration: 90+ minutes (~15,000+ words).
"""
        else:
            format_guideline = """
FORMAT REQUIREMENT — MULTI-SERIES EPISODIC (IN SAME FILE):
- Structure this as a MULTI-SERIES with distinct parts (e.g. PART 1: THE DISCOVERY, PART 2: THE CONFRONTATION).
- Each part must deliver 50+ minutes of suspenseful, gripping narrative.
- STRICT RULE: NO SCI-FI. Keep the narrative grounded in horror, true crime, history, or real-world suspense.
"""

        dialogue_instructions = ""
        if multi_voice or style in ["fiction_dramatized", "mafia_werewolf"]:
            dialogue_instructions = """
MULTI-VOICE CHARACTER DIALOGUE FORMAT:
- Tag spoken lines by character tag so the TTS engine can assign separate male and female actors:
  [NARRATOR]: For scene narration and atmospheric descriptions.
  [MALE_LEAD]: For the male protagonist or male speaking characters.
  [FEMALE_LEAD]: For the female protagonist or female speaking characters.
  [ANTAGONIST]: For villains, rival alphas, or treacherous figures.
- Keep dialogue punchy, realistic, and emotionally reactive.
"""

        context_prompt = ""
        if episode_context:
            context_prompt = f"""
EPISODIC / MULTI-SERIES CONTEXT:
Previous Events / Lore Summary: {episode_context}
- Open with a connection to previous events and escalate into the next chapter.
"""

        prompt = f"""
You are an elite YouTube storyteller and scriptwriter specializing in high-retention long-form audio narratives and podcasts.

Topic / Premise: {topic}
Story Framework: {style_desc}
Target Duration: {duration_str} minutes minimum ({min_words} to {max_words} words)

{format_guideline}
{context_prompt}
{dialogue_instructions}

RETENTION-ENGINEERED NARRATIVE ARCHITECTURE (BASED ON YOUTUBE ALGORITHMIC METRICS):
1. THE 30-SECOND COLD-OPEN HOOK:
   - ZERO PREAMBLE. No greetings ("Hey guys"), no channel introductions, no Reddit meta-filler ("Throwaway account here").
   - Open IN MEDIA RES right at the instant of moral outrage, shocking discovery, or pivotal betrayal.
   - Introduce an unresolved curiosity gap immediately so viewers are cognitively invested from second one.
   - Keep opening 30 seconds psychologically gripping but clean of graphic gore or profanity for advertiser safety.

2. THE SETUP & RELATIONAL GROUNDING (Minutes 1–3):
   - Ground the listener in the protagonist's world, their loyalty, and what is at stake right before the facade collapses.

3. NESTED NARRATIVE LOOPS (Every 8–10 Minutes):
   - Never allow all storylines to flatline. As one secondary mystery or confrontation resolves, open an adjacent, higher-stakes complication before the first settles.
   - Prevent listener exit points.

4. MID-ROLL AD RETENTION ANCHORS (At roughly 15%, 30%, 50%, 75% marks):
   - Build deliberate narrative escalations, sudden arrivals, or new discoveries directly preceding natural mid-roll break points.

5. THE CLIMAX & COMPENSATORY JUSTICE:
   - Deliver decisive, cathartic retribution. The villain/betrayer faces complete financial, legal, and social consequences.
   - Protagonist emerges dignified, independent, and victorious.

STRICT CONSTRAINTS:
- ABSOLUTELY NO SCI-FI, SPACE, CYBERPUNK, OR SCI-FI MOVIE ELEMENTS.
- Integrate vocal nuances like [pause], [sigh], [whisper], [gasp] naturally at high-emotion moments.
- Output ONLY the story script. Plain text narrative. Do NOT include markdown meta-analysis or writer notes.
- Target word count: approximately {min_words} to {max_words} words.
"""

        print(f"\n[INFO] Contacting NVIDIA NIM ({self.model}) for a {duration_str}-min story...")
        story_text = ""
        # Sanitize topic for temporary file path
        safe_topic_slug = re.sub(r'[^\w-]', '_', topic[:20]).strip('_') or "narrative"
        partial_path = f"story_partial_{safe_topic_slug}.txt"

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                top_p=0.95,
                max_tokens=16384,
                stream=True
            )
            for chunk in completion:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content is not None:
                    print(content, end="", flush=True)
                    story_text += content
                    # save partial every ~500 chars so a crash doesn't lose work
                    if len(story_text) % 500 < 10:
                        with open(partial_path, "w", encoding="utf-8") as f:
                            f.write(story_text)

            if os.path.exists(partial_path):
                os.remove(partial_path)  # clean up on success

            # strip <think>...</think> blocks (leaked reasoning from models)
            story_text = re.sub(r'<think>.*?</think>', '', story_text, flags=re.DOTALL)
            story_text = re.sub(r'^.*?</think>', '', story_text, flags=re.DOTALL)
            story_text = story_text.strip()

            return story_text
        except Exception as e:
            print(f"\n[ERROR] NVIDIA NIM generation failed: {e}")
            if story_text:
                print(f"[INFO] Partial story saved to {partial_path}")
            return story_text or None
