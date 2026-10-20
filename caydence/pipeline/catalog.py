"""
Catalog and Registry Management for Caydence Master Story Catalog.
"""

import os
import re

# Repository paths
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(MODULE_DIR))
STORY_IDEAS_FILE = os.environ.get("CAYDENCE_CATALOG_FILE") or os.path.join(REPO_ROOT, "story_ideas.txt")

class StoryType:
    """Hardcoded Three-Tier Production Taxonomy for Caydence Stories."""
    TYPE_1 = "Type 1"  # Normal / Solo-Narrator Confession & Story (50+ min)
    TYPE_2 = "Type 2"  # Multi-People Cinematic Audio Drama (stems, cues, spatial FX)
    TYPE_3 = "Type 3"  # Reserved (Custom user format)

    ALL_TYPES = [TYPE_1, TYPE_2, TYPE_3]

    @classmethod
    def normalize(cls, val):
        """Converts strings, integers, or aliases into standard 'Type 1', 'Type 2', or 'Type 3'."""
        if val is None:
            return cls.TYPE_1
        v = str(val).strip().lower()
        if v in ["1", "type1", "type 1", "type_1", "normal"]:
            return cls.TYPE_1
        if v in ["2", "type2", "type 2", "type_2", "drama", "experiment", "multi"]:
            return cls.TYPE_2
        if v in ["3", "type3", "type 3", "type_3"]:
            return cls.TYPE_3
        return cls.TYPE_1


# Hardcoded Curated Registry for Type 2 (Survival Rules & Situational Protocols - 50+ min)
TYPE_2_REGISTRY = {
    1: {
        "title": "The Wheeler Highrise Protocol",
        "slug": "TheWheelerHighriseProtocol",
        "gender": "female",
        "type": StoryType.TYPE_2,
        "hook": "A freelance draftsman desperate for affordable downtown living signs a dirt-cheap lease on the 39th floor of Wheeler Towers, bound by 5 mandatory night rules: lock the triple deadbolts before midnight, never drink the red-tinted tap water, keep the blinds drawn against figures outside the 39th-floor window, answer the hallway phone only when it rings at 3:33 AM, and always take the emergency stairwell if the building shudders.",
        "cast": ["thomas", "mario", "sally"]
    },
    2: {
        "title": "Night Shift at St. Jude's Ward 4",
        "slug": "NightShiftAtStJudesWard4",
        "gender": "female",
        "type": StoryType.TYPE_2,
        "hook": "An agency nurse accepts a $95/hr contract watching a condemned, sealed tuberculosis wing scheduled for demolition, provided she follows 6 strict rules: never answer call lights from room 412, turn off the hallway fluorescents if gurney wheels roll toward the station, and never record the vitals of anyone who knows her full legal name.",
        "cast": ["elena", "dr_vance", "orderly_jack"]
    },
    3: {
        "title": "The Blackwood Tollway Booth 9",
        "slug": "TheBlackwoodTollwayBooth9",
        "gender": "male",
        "type": StoryType.TYPE_2,
        "hook": "A college student takes the graveyard shift on an abandoned mountain bypass road that only gets three vehicles a night, with 5 mandatory rules: never make eye contact through tinted driver windows, drop pre-1940 silver coins into the lead lockbox without counting, and never raise the boom gate when the mountain horn blows.",
        "cast": ["marcus", "supervisor_dan", "stranger"]
    },
    4: {
        "title": "The Tenant of Heron Point Light",
        "slug": "TheTenantOfHeronPointLight",
        "gender": "male",
        "type": StoryType.TYPE_2,
        "hook": "A marine diesel mechanic takes a high-paying winter contract at an isolated cliffside beacon where the previous two keepers vanished, under 6 strict guidelines: keep the brass lantern lit, never look down the cliff stairwell when the low-tide bell tolls, and bolt the trapdoor when the offshore wind reverses direction.",
        "cast": ["arthur", "harbor_master", "radio_op"]
    },
    5: {
        "title": "Night Auditor at Hotel Vandermeer",
        "slug": "NightAuditorAtHotelVandermeer",
        "gender": "female",
        "type": StoryType.TYPE_2,
        "hook": "A night auditor takes over the desk of an opulent 1928 Art Deco hotel holding an unindexed ledger of missing guests and a master key, governed by 7 protocols: never inspect room service trays outside suite 704, answer the penthouse rotary line only by quoting the standard room rate, and verify the ballroom doors remain padlocked from the exterior when the organ plays.",
        "cast": ["claire", "concierge_leo", "guest_704"]
    },
    6: {
        "title": "Sub-Level 3 Security at Greyfriars Legal Archive",
        "slug": "SubLevel3SecurityAtGreyfriarsArchive",
        "gender": "male",
        "type": StoryType.TYPE_2,
        "hook": "A night guard monitors underground microfilm storage vaults beneath an ancient commercial bank, under 5 strict directives: verify your reflection in the mirror before entering Vault C, leave clean paper on the threshold if an empty typewriter begins typing, and never open cage 14 after 2:00 AM.",
        "cast": ["david", "maya", "curator_thorne"]
    },
    7: {
        "title": "Caretaker of Blackthorn Orchard",
        "slug": "CaretakerOfBlackthornOrchard",
        "gender": "male",
        "type": StoryType.TYPE_2,
        "hook": "A groundskeeper accepts free cottage lodging and a lucrative stipend to watch a 400-acre hollow orchard off-season, under 6 vital rules: never touch windfallen fruit after dusk, cover all mirrors if the heavy orchard bell tolls without wind, and ignore any frantic knocking from inside the root cellar.",
        "cast": ["thomas", "proprietor_reed", "neighbor"]
    },
    8: {
        "title": "Platform 0 at Lancaster Junction",
        "slug": "Platform0AtLancasterJunction",
        "gender": "female",
        "type": StoryType.TYPE_2,
        "hook": "A midnight switchboard operator at a remote rail depot oversees unlisted freight routing, under 5 strict safety rules: log any dark, unlit passenger train arriving at Platform 0 as 'Signal Drift', refuse passenger tickets bearing dates earlier than 1914, and step back from the observation glass if figures stand motionless on the rails.",
        "cast": ["maya", "dispatcher_cole", "conductor"]
    },
    9: {
        "title": "The Night Watch at Bell Foundry",
        "slug": "TheNightWatchAtBellFoundry",
        "gender": "male",
        "type": StoryType.TYPE_2,
        "hook": "A patrol watchman guards a 150-year-old bronze foundry casting cathedral bells, under 6 rigid rules: douse the cooling pits immediately if an unclappered bell rings, never step across the chalk line after midnight, and verify your partner's face in direct light if they call your name from around a blind corner.",
        "cast": ["marcus", "foreman_elias", "partner_bill"]
    },
    10: {
        "title": "The Winter Caretaker of Camp Oakhaven",
        "slug": "TheWinterCaretakerOfCampOakhaven",
        "gender": "female",
        "type": StoryType.TYPE_2,
        "hook": "A solo caretaker watches a snowbound forestry camp deep in the Adirondack mountains during a blizzard, under 7 survival protocols: never start the generator if children's laughter echoes from the dark dining hall, keep the boots on the front mat counted at all times, and never look toward the ceiling if fresh footprints lead into the cabin and stop beside the bed.",
        "cast": ["elena", "ranger_keller", "sheriff"]
    }
}

# Hardcoded Curated Registry for Type 3 (The Department of Unlisted Assets - DUA Case Files - 50+ min)
TYPE_3_REGISTRY = {
    1: {
        "title": "Case 401: The Blackwood Sinkhole",
        "slug": "Case401TheBlackwoodSinkhole",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "March 10, 1987",
        "location": "Blackwood Limestone Quarry, Pennsylvania",
        "hook": "When a limestone quarry in rural Pennsylvania collapses to expose a perfectly cylindrical vertical shaft marked with repeating Roman numerals, DUA Field Agent Miller and Archivist Vance deploy with acoustic reel-to-reel recorders to document the subterranean void before municipal surveyors find it.",
        "cast": ["agent_miller", "archivist_vance", "foreman_quarry"]
    },
    2: {
        "title": "Case 402: The Unrecorded Room",
        "slug": "Case402TheUnrecordedRoom",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "February 15, 1954",
        "location": "East Wing Masonry, Greenfield County Courthouse, Iowa",
        "hook": "During renovations of a 1910 county courthouse, an architect detects a 400-square-foot void between exterior masonry and structural blueprints; DUA agents breach the wall to find a furnished room with warm coffee and a radio playing broadcasts from 1954.",
        "cast": ["agent_vance", "surveyor_davies", "architect_ross"]
    },
    3: {
        "title": "Case 403: The Cold Spring Wiretaps",
        "slug": "Case403TheColdSpringWiretaps",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "February 23, 1983",
        "location": "Cold Spring County Telephone Exchange, New York",
        "hook": "A county telephone exchange intercepts steady conversations between private numbers disconnected thirty years ago; DUA wiretap logs reveal the voices are describing the current, private real-time movements of residents sleeping in the town.",
        "cast": ["analyst_briggs", "agent_miller", "operator_hannah"]
    },
    4: {
        "title": "Case 404: The Well of Saint Jude",
        "slug": "Case404TheWellOfSaintJude",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "October 10, 1985",
        "location": "Municipal Well of Saint Jude, New England",
        "hook": "DUA medical investigator Dr. Hargrave arrives in an isolated mountain village where municipal tap water has thickened to the viscosity of mineral oil, discovering rapid bone crystallization among residents who drank from the town well.",
        "cast": ["dr_hargrave", "agent_miller", "parish_priest"]
    },
    5: {
        "title": "Case 405: The Mirror in Cell 19",
        "slug": "Case405TheMirrorInCell19",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "June 19, 1979",
        "location": "Solitary Cell 19, Blackwood Maximum Security Prison",
        "hook": "In a shuttered maximum security prison, the polished steel mirror in solitary cell 19 reflects the room with an exact 4-second delay; audio interrogation logs reveal an inmate whose reflection refused to follow his physical movements.",
        "cast": ["inquisitor_thorne", "warden_graves", "inmate_19"]
    },
    6: {
        "title": "Case 406: The Vanishing 4:15",
        "slug": "Case406TheVanishing415",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "December 13, 1972",
        "location": "Dismantled Rail Line, Upstate Corridor",
        "hook": "A commuter train engine and three passenger cars disappear from upstate rail line every Tuesday at 4:15 AM without tripping signals, only for its whistle to be recorded echoing over empty cornfields where tracks were dismantled fifty years earlier.",
        "cast": ["agent_vance", "operator_jenkins", "stationmaster"]
    },
    7: {
        "title": "Case 407: The Hollow Forest Survey",
        "slug": "Case407TheHollowForestSurvey",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "March 10, 1975",
        "location": "12-Square-Mile Timberland Tract, Maine",
        "hook": "A geodetic survey team investigates a 12-square-mile tract of Maine timberland where environmental sound drops by 45 decibels, discovering centuries-old hemlocks with completely hollowed trunks functioning as organic acoustic resonance chambers.",
        "cast": ["surveyor_davies", "agent_miller", "botanist_reed"]
    },
    8: {
        "title": "Case 408: The 1974 Civil Defense Broadcast",
        "slug": "Case408The1974CivilBroadcast",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "July 15, 1974",
        "location": "UHF Relay Tower 8, West Virginia",
        "hook": "A rural UHF relay tower repeatedly transmits an automated civil defense emergency evacuation order recorded in 1974 for a catastrophic event that the federal government officially logged as a routine fifteen-minute thunderstorm.",
        "cast": ["analyst_briggs", "archivist_vance", "engineer_clark"]
    },
    9: {
        "title": "Case 409: The Wax Cylinder Inquest",
        "slug": "Case409TheWaxCylinderInquest",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "October 9, 1898",
        "location": "Waverly Sanitarium Archives, Massachusetts",
        "hook": "DUA Archivist Vance unseals an uncataloged 1898 Edison wax cylinder recorded inside a private sanitarium; anyone who listens to the needle tracking across the grooves loses all short-term memories of the preceding two hours.",
        "cast": ["archivist_vance", "inquisitor_thorne", "dr_asylum"]
    },
    10: {
        "title": "Case 410: The Breach at Sub-Basement 6",
        "slug": "Case410TheBreachAtSubBasement6",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "October 10, 1980",
        "location": "Sub-Basement 6, DUA Central Facility, Maryland",
        "hook": "When a regional grid failure cuts secondary auxiliary power to DUA's central storage facility in Maryland, pneumatic seals on containment vaults 401 through 409 depressurize, forcing surviving personnel to execute the 1952 Acoustic Lockdown Protocol in complete darkness.",
        "cast": ["director_redfield", "agent_miller", "archivist_vance", "dr_hargrave"]
    },
    11: {
        "title": "Case 411: The Unmapped Beacon of Cape Despair",
        "slug": "Case411TheUnmappedBeaconOfCapeDespair",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "March 10, 1938",
        "location": "Decommissioned Granite Lighthouse, Cape Despair",
        "hook": "An offshore granite lighthouse decommissioned in 1938 begins emitting focused ultraviolet light pulses visible only on naval radar, transmitting Morse code maritime coordinates for a cargo freighter that ran aground in 1886.",
        "cast": ["agent_vance", "navigator_crawford", "keeper_alden"]
    },
    12: {
        "title": "Case 412: The Blackwood Microfilm Archive",
        "slug": "Case412TheBlackwoodMicrofilmArchive",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "October 12, 1982",
        "location": "Off-Limits Microfilm Vault, Miskatonic University Library",
        "hook": "A university archivist discovers three unlabeled spools of 16mm microfilm in an off-limits sub-basement vault; whenever viewed on the projector, the scanned newspapers depict obituary notices for people currently alive in the reading room.",
        "cast": ["archivist_vance", "agent_miller", "librarian_hollis"]
    },
    13: {
        "title": "Case 413: The Silent Frequency of Tower 9",
        "slug": "Case413TheSilentFrequencyOfTower9",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "October 13, 1983",
        "location": "Lookout Tower 9, Cascade Mountain Range",
        "hook": "A high-altitude forest service fire lookout tower in the Cascades reports hearing steady telephone dial tones and human breathing from its unpowered lightning rod during severe electrical storms.",
        "cast": ["agent_vance", "ranger_keller", "technician_morse"]
    },
    14: {
        "title": "Case 414: The 03:00 Sub-Surface Seismic Record",
        "slug": "Case414The0300SubSurfaceSeismicRecord",
        "gender": "male",
        "type": StoryType.TYPE_3,
        "date": "October 31, 1978",
        "location": "Appalachian Sub-Surface Seismic Vault, Virginia",
        "hook": "Seismographs across three Appalachian research stations register identical rhythmic micro-tremors every night at precisely 03:00 AM, matching the acoustic tempo of a massive human heartbeat located 4,000 feet beneath granite bedrock.",
        "cast": ["agent_miller", "geophysicist_stone", "director_redfield"]
    },
    15: {
        "title": "Case 415: The Unopened Safe of Room 104",
        "slug": "Case415TheUnopenedSafeOfRoom104",
        "gender": "female",
        "type": StoryType.TYPE_3,
        "date": "October 15, 1935",
        "location": "Room 104, Hillside Sanatorium",
        "hook": "In a sealed wing of an abandoned 1930s sanitarium slated for demolition, a floor-mounted iron safe cannot be drilled or moved; stethoscope analysis reveals steady rotary phone ringing and an operator's voice whispering from inside the steel chamber.",
        "cast": ["agent_vance", "inquisitor_thorne", "demolition_foreman"]
    }
}

# Curated Primary 20 Stories from story_ideas.txt with explicit gender & slugs (Type 1)
STORY_REGISTRY = {
    1: {
        "title": "A Billionaire's Revenge: When I Walked Away",
        "slug": "WhenIWalkedAway",
        "gender": "male",
        "hook": "Groom walks away quietly when bride asks her lover to stand in as groom; takes his investment portfolio with him."
    },
    2: {
        "title": "He Was by Her Side on Our Wedding Day",
        "slug": "ByHerSide",
        "gender": "female",
        "hook": "Bride overhears fiancé promising his pregnant childhood friend that the marriage is just for business; walks out into a new life."
    },
    3: {
        "title": "After My Groom Abandoned Me, His Rival Married Me",
        "slug": "AfterMyGroomAbandonedMeHisRivalMarriedMe",
        "gender": "female",
        "hook": "Left at cathedral doors, she turns to rival executive in the third row and makes an on-the-spot proposal that changes both their lives."
    },
    4: {
        "title": "After the Groom Ran Away, I Married His Estranged Father",
        "slug": "AfterTheGroomRanAwayIMarriedHisEstrangedFather",
        "gender": "female",
        "hook": "Standing in front of 200 guests as fiancé elopes with her cousin, she exposes the embezzlement scheme funded by his family trust."
    },
    5: {
        "title": "Eight Years as His Second Choice",
        "slug": "EightYearsAsHisSecondChoice",
        "gender": "female",
        "hook": "During his company launch party, she hears him introduce his first love as his sole inspiration; drops resignation and ring into his glass."
    },
    6: {
        "title": "After I Married the Boss, My Childhood Sweetheart Begged for Mercy",
        "slug": "AfterIMarriedTheBossMyChildhoodSweetheartBegged",
        "gender": "female",
        "hook": "Dismissed as uneducated by fiancé's elite family, she walks away to take over her grandfather's maritime empire."
    },
    7: {
        "title": "My Groom Lost Me on Our Wedding Day",
        "slug": "MyGroomLostMeOnOurWeddingDay",
        "gender": "female",
        "hook": "Groom demands she sign a post-nuptial waiver surrendering her mother's home 30 minutes before march; she cancels the reception and leaves."
    },
    8: {
        "title": "Betrayed Before the Altar, Claimed by the Chairman",
        "slug": "BetrayedBeforeTheAltarClaimedByTheChairman",
        "gender": "female",
        "hook": "She finds nanny-cam footage showing maid of honor rehearsing vows in her bridal gown; live-streams it to church projector."
    },
    9: {
        "title": "The Betrayed Bride Wakes Before the Wedding",
        "slug": "TheBetrayedBrideWakesBeforeTheWedding",
        "gender": "female",
        "hook": "Discovering fiancé booked flights for two to Maldives under another woman's name, she cancels reception and books a one-way trip to Tokyo."
    },
    10: {
        "title": "Bride of Betrayal: The Thirty-Day Silent Exit",
        "slug": "BrideOfBetrayalTheThirtyDaySilentExit",
        "gender": "female",
        "hook": "After catching him red-handed, she spends 30 calm days quietly liquidating joint assets before vanishing on rehearsal morning."
    },
    11: {
        "title": "Betrayed Bride's Kenyan Flight",
        "slug": "BetrayedBridesKenyanFlight",
        "gender": "female",
        "hook": "Humiliated by groom's family at altar, she transfers agricultural tech patent to a Nairobi enterprise and leaves them facing bankruptcy."
    },
    12: {
        "title": "The Revenge of the Betrayed Bride: Stock Market Reckoning",
        "slug": "TheRevengeOfTheBetrayedBride",
        "gender": "female",
        "hook": "Groom marries another woman for social standing; she short-sells his family conglomerate's stock on Monday morning."
    },
    13: {
        "title": "Betrayed, Broken, Married Up",
        "slug": "BetrayedBrokenMarriedUp",
        "gender": "female",
        "hook": "Groom's mother demands she surrender salary to future sister-in-law; walks out and accepts an overseas leadership post with his parent company."
    },
    14: {
        "title": "Left at the Altar: The Silent Architect's Payback",
        "slug": "LeftAtTheAltarTheSilentArchitect",
        "gender": "female",
        "hook": "Architect bride is abandoned on wedding day; enforces copyright clause on multi-million-dollar estate she designed for him."
    },
    15: {
        "title": "Betrayed at the Altar, A Vengeful 'I Do'",
        "slug": "BetrayedAtTheAltarAVengefulIDo",
        "gender": "female",
        "hook": "Groom abandons her for his ex; she signs a contract partnership with venture capitalist who came to watch him fall."
    },
    16: {
        "title": "The Bride They Replaced Became the Heir",
        "slug": "TheBrideTheyReplacedBecameTheHeir",
        "gender": "female",
        "hook": "Stepfamily swaps her out to seat stepsister; 30 minutes later, probate court reveals she is sole executor of the dynasty."
    },
    17: {
        "title": "Only Me to Count On: The Five-Year Disappearance",
        "slug": "OnlyMeToCountOnTheFiveYearDisappearance",
        "gender": "female",
        "hook": "Banished when sister steals fiancé, she returns as silent majority partner buying out their failing business."
    },
    18: {
        "title": "I Was Already Gone When He Decided to Love Me",
        "slug": "IWasAlreadyGoneWhenHeDecidedToLoveMe",
        "gender": "female",
        "hook": "After 5 years of being treated as invisible, packs two suitcases while he is at mistress's dinner, leaving no forwarding address."
    },
    19: {
        "title": "She Stole My Wedding, So I Took Her Trust Fund",
        "slug": "SheStoleMyWeddingSoITookHerTrustFund",
        "gender": "female",
        "hook": "Stepsister secretly wears her custom designer dress to rehearsal; bride reveals stepsister's fraudulent accounting to tax authority."
    },
    20: {
        "title": "She Stole My Wedding, So I Left",
        "slug": "SheStoleMyWeddingSoILeft",
        "gender": "female",
        "hook": "Groom's sister pins family heirloom veil on childhood friend in bridal suite; bride Claire silently walks out and revokes luxury brownstone deed."
    }
}

class StoryCatalog:
    """Provides lookup and parsing for all 100 story titles in the master catalog."""

    @staticmethod
    def _slugify(text):
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        words = clean.split()
        return "".join(w.capitalize() for w in words[:6])

    @classmethod
    def get_story(cls, sid: int, story_type: str = None) -> dict:
        """Returns normalized metadata dictionary for a given story ID and type."""
        norm_type = StoryType.normalize(story_type) if story_type else None

        # Approved Voice Pools (User Selected)
        MALE_VOICES = ["en-US-BrianNeural", "en-US-SteffanNeural", "en-CA-LiamNeural"]
        FEMALE_VOICES = ["en-US-JennyNeural", "en-US-AnaNeural"]

        def _resolve_narrator(g, sid_num):
            g_clean = (g or "male").lower()
            if g_clean == "female":
                return FEMALE_VOICES[(sid_num // 2) % len(FEMALE_VOICES)]
            else:
                return MALE_VOICES[(sid_num // 2) % len(MALE_VOICES)]

        # Check Type 2 registry if requested or if sid matches Type 2
        if norm_type == StoryType.TYPE_2:
            if sid in TYPE_2_REGISTRY:
                data = TYPE_2_REGISTRY[sid].copy()
                data["sid"] = sid
                data["type"] = StoryType.TYPE_2
                data["voice"] = _resolve_narrator(data.get("gender"), sid)
                return data
            # Fallback to adapting base story into a Type 2 drama
            base = cls.get_story(sid, story_type=StoryType.TYPE_1)
            base["type"] = StoryType.TYPE_2
            base["voice"] = _resolve_narrator(base.get("gender"), sid)
            return base

        # Type 3 (The Department of Unlisted Assets - DUA Case Files)
        if norm_type == StoryType.TYPE_3:
            if sid in TYPE_3_REGISTRY:
                data = TYPE_3_REGISTRY[sid].copy()
                data["sid"] = sid
                data["type"] = StoryType.TYPE_3
                data["voice"] = _resolve_narrator(data.get("gender"), sid)
                return data
            base = cls.get_story(sid, story_type=StoryType.TYPE_1)
            base["type"] = StoryType.TYPE_3
            base["voice"] = _resolve_narrator(base.get("gender"), sid)
            return base

        # Default: Type 1 Lookup
        if sid in STORY_REGISTRY:
            data = STORY_REGISTRY[sid].copy()
            data["sid"] = sid
            data["type"] = StoryType.TYPE_1
            data["voice"] = _resolve_narrator(data.get("gender"), sid)
            return data

        # If not in curated 20, dynamically parse from story_ideas.txt
        all_stories = cls.load_catalog_file()
        if sid in all_stories:
            data = all_stories[sid].copy()
            data["sid"] = sid
            data["type"] = StoryType.TYPE_1
            data["voice"] = _resolve_narrator(data.get("gender"), sid)
            return data

        raise KeyError(f"Story ID #{sid} not found in master catalog.")

    @classmethod
    def get_catalog_size(cls, story_type: str = None) -> int:
        """Returns the registered number of curated stories for a given tier."""
        norm = StoryType.normalize(story_type) if story_type else None
        if norm == StoryType.TYPE_2:
            return len(TYPE_2_REGISTRY)
        if norm == StoryType.TYPE_3:
            return len(TYPE_3_REGISTRY)
        if norm == StoryType.TYPE_1:
            return max(len(cls.load_catalog_file()), 100)
        return len(cls.load_catalog_file())

    @classmethod
    def get_folder_name(cls, sid: int, sinfo: dict) -> str:
        """Standardized directory naming convention: {sid}-{slug} (e.g. 1-TheWheelerHighriseProtocol)"""
        slug = sinfo.get("slug") or cls._slugify(sinfo.get("title", f"Story{sid}"))
        return f"{sid}-{slug}"

    @classmethod
    def get_audio_filename(cls, sid: int, sinfo: dict, season: int = 1) -> str:
        """Standardized universal audio filename convention: T{type}S{season}E{episode}-{StoryName}.wav
        Example: T3S1E1-TheBlackwoodSinkhole.wav
        """
        stype_str = sinfo.get("type") or StoryType.TYPE_1
        t_num = 1
        if "3" in str(stype_str):
            t_num = 3
        elif "2" in str(stype_str):
            t_num = 2
        elif "1" in str(stype_str):
            t_num = 1

        title = sinfo.get("title", f"Story{sid}")
        # If title has "Case XXX: ...", extract the short title after colon
        m = re.search(r'Case\s+\d+:\s*(.+)$', title, re.IGNORECASE)
        if m:
            clean_title = m.group(1).strip()
        else:
            clean_title = title

        # Strip prefixes like reddit-
        clean_title = re.sub(r'(?i)^reddit[-\s_]*', '', clean_title)
        words = re.findall(r'[A-Za-z0-9]+', clean_title)
        slug = "".join(w.capitalize() if not (w.isupper() and len(w) > 1) else w for w in words)
        if not slug:
            slug = f"Story{sid}"

        return f"T{t_num}S{season}E{sid}-{slug}.wav"

    @classmethod
    def get_output_folder(cls, output_base: str, sid: int, sinfo: dict) -> str:
        """Resolves target output path partitioned by hardcoded story type."""
        stype = sinfo.get("type") or StoryType.TYPE_1
        folder_name = cls.get_folder_name(sid, sinfo)
        return os.path.join(output_base, stype, folder_name)

    _DIR_CACHE = {}

    @classmethod
    def find_existing_folder(cls, output_base: str, sid: int, sinfo: dict) -> str:
        """Finds existing output directory for story ID, handling slug and prefix variations."""
        stype = sinfo.get("type") or StoryType.TYPE_1
        canonical = cls.get_output_folder(output_base, sid, sinfo)
        if os.path.exists(canonical):
            return canonical

        type_dir = os.path.join(output_base, stype)
        if type_dir not in cls._DIR_CACHE:
            cls._DIR_CACHE[type_dir] = os.listdir(type_dir) if os.path.exists(type_dir) else []
        for candidate in cls._DIR_CACHE[type_dir]:
            if candidate == str(sid) or candidate.startswith(f"{sid}-"):
                c_path = os.path.join(type_dir, candidate)
                if os.path.isdir(c_path):
                    return c_path

        legacy = os.path.join(output_base, cls.get_folder_name(sid, sinfo))
        if os.path.exists(legacy):
            return legacy

        if output_base not in cls._DIR_CACHE:
            cls._DIR_CACHE[output_base] = os.listdir(output_base) if os.path.exists(output_base) else []
        for candidate in cls._DIR_CACHE[output_base]:
            if candidate == str(sid) or candidate.startswith(f"{sid}-"):
                c_path = os.path.join(output_base, candidate)
                if os.path.isdir(c_path):
                    return c_path

        return canonical


    @classmethod
    def load_catalog_file(cls) -> dict:
        """Parses story_ideas.txt and returns all indexed stories."""
        if not os.path.exists(STORY_IDEAS_FILE):
            return STORY_REGISTRY.copy()

        stories = {}
        current_sid = None
        current_title = ""
        current_hook = ""

        with open(STORY_IDEAS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line_str = line.strip()
            # Match: "1.  A Billionaire's Revenge..." or "20. She Stole..."
            m = re.match(r'^(\d+)\.\s+(.+)$', line_str)
            if m:
                if current_sid is not None and current_title:
                    stories[current_sid] = cls._build_entry(current_sid, current_title, current_hook)

                current_sid = int(m.group(1))
                raw_title = m.group(2)
                # Strip out [PRODUCED: ...] notes from title
                current_title = re.sub(r'\s*—\s*\[.*\]$', '', raw_title).strip()
                current_hook = ""
                continue

            if current_sid is not None and line_str.startswith("Hook"):
                current_hook = re.sub(r'^Hook(?:\s*\([^)]*\))?:\s*', '', line_str).strip()

        if current_sid is not None and current_title:
            stories[current_sid] = cls._build_entry(current_sid, current_title, current_hook)

        # Merge curated registry over parsed items to preserve high-fidelity hooks
        for sid, curated in STORY_REGISTRY.items():
            stories[sid] = curated.copy()
            stories[sid]["sid"] = sid
            stories[sid]["type"] = StoryType.TYPE_1

        return stories

    @classmethod
    def _build_entry(cls, sid, title, hook):
        # Infer gender from title and hook keywords
        text = f"{title} {hook}".lower()
        if any(w in text for w in ["bride", "she", "her", "stepsister", "mother", "wife", "mistress"]):
            gender = "female"
        elif any(w in text for w in ["groom", "he", "his", "husband", "father", "billionaire's revenge: when i walked"]):
            gender = "male"
        else:
            gender = "female"

        return {
            "title": title,
            "slug": cls._slugify(title),
            "gender": gender,
            "type": StoryType.TYPE_1,
            "hook": hook or f"Narrative one-shot following {title}."
        }
