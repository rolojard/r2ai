"""
Star Wars Character Database for R2-D2 Recognition System
========================================================

Comprehensive database of Star Wars characters with R2-D2 specific relationship data,
visual descriptors, and reaction patterns based on canon sources.

This database includes characters from:
- Original Trilogy (Episodes IV-VI)
- Prequel Trilogy (Episodes I-III)
- Sequel Trilogy (Episodes VII-IX)
- The Clone Wars, Rebels, and other canon media
"""

from star_wars_character_database_schema import *
from datetime import datetime


def create_star_wars_character_database() -> CharacterDatabase:
    """Create and populate the complete Star Wars character database"""
    db = CharacterDatabase()

    # === ORIGINAL TRILOGY CORE CHARACTERS ===

    # Luke Skywalker - R2-D2's closest friend and primary master
    luke = StarWarsCharacter(
        name="Luke Skywalker",
        faction=FactionAlignment.JEDI,
        relationship_to_r2d2=RelationshipType.CLOSE_FRIEND,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.EXCITED_BEEPS,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Happy ascending whistles with excited chirps",
            behavioral_notes="R2-D2 becomes very animated, extends periscope, rocks back and forth",
            confidence_modifier=1.2
        ),
        visual_descriptor=VisualDescriptor(
            primary_outfit="Black Jedi robes",
            distinctive_features=["blonde hair", "blue eyes", "Jedi lightsaber"],
            height_range=(172, 172),
            hair_color="blonde",
            eye_color="blue",
            species="human",
            notable_accessories=["lightsaber", "Jedi robes", "utility belt"],
            costume_variations=["farmboy tunic", "Rebel pilot suit", "Bespin fatigues", "Endor camouflage", "black Jedi outfit"]
        ),
        timeline=CharacterTimeline(
            original_era=True,
            sequel_era=True,
            tv_series=["The Mandalorian", "The Book of Boba Fett"]
        ),
        aliases=["Luke", "Red Five", "Jedi Luke"],
        full_name="Luke Skywalker",
        titles=["Jedi Knight", "Jedi Master", "Commander"],
        species="human",
        homeworld="Tatooine",
        trust_level=10,
        first_meeting_context="Owen Lars' moisture farm on Tatooine",
        recognition_priority=10,
        confidence_threshold=0.85,
        canon_status="canon",
        notes="R2-D2's primary companion and closest friend. Luke learned to understand Binary over time."
    )

    # Princess Leia - R2-D2's original mission recipient
    leia = StarWarsCharacter(
        name="Leia Organa",
        aliases=["Princess Leia", "Leia", "General Organa"],
        full_name="Leia Organa Skywalker Solo",
        titles=["Princess of Alderaan", "General", "Senator"],
        faction=FactionAlignment.REBEL_ALLIANCE,
        species="human",
        homeworld="Alderaan",
        relationship_to_r2d2=RelationshipType.CLOSE_FRIEND,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.EXCITED_BEEPS,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES, EmotionalResponse.CAUTIOUS_CHIRPS],
            sound_pattern="Respectful whistles with underlying excitement",
            behavioral_notes="Formal acknowledgment beeps followed by warmer sounds as relationship develops",
            confidence_modifier=1.1
        ),
        trust_level=9,
        visual_descriptor=VisualDescriptor(
            primary_outfit="White Alderaanian dress",
            distinctive_features=["brown hair in side buns", "brown eyes", "royal bearing"],
            height_range=(150, 150),
            hair_color="brown",
            eye_color="brown",
            species="human",
            notable_accessories=["blaster", "comlink", "royal jewelry"],
            costume_variations=["white gown", "Hoth combat gear", "Endor camouflage", "Boushh disguise", "Resistance general uniform"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,  # Brief appearance as baby
            original_era=True,
            sequel_era=True
        ),
        first_meeting_context="Death Star plans mission aboard Tantive IV",
        recognition_priority=10,
        confidence_threshold=0.80,
        canon_status="canon",
        notes="R2-D2's original mission was to deliver her message to Obi-Wan Kenobi"
    )

    # Han Solo - Trusted friend and pilot of the Millennium Falcon
    han = StarWarsCharacter(
        name="Han Solo",
        aliases=["Han", "Captain Solo"],
        full_name="Han Solo",
        titles=["Captain", "General"],
        faction=FactionAlignment.REBEL_ALLIANCE,
        species="human",
        homeworld="Corellia",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.PLAYFUL_TRILLS,
            secondary_emotions=[EmotionalResponse.CAUTIOUS_CHIRPS],
            sound_pattern="Amused warbles with occasional sarcastic beeps",
            behavioral_notes="R2-D2 often acts mischievous around Han, sometimes ignoring direct orders",
            confidence_modifier=0.9
        ),
        trust_level=8,
        visual_descriptor=VisualDescriptor(
            primary_outfit="White shirt with black vest",
            distinctive_features=["dark hair", "brown eyes", "cocky smile", "DL-44 blaster"],
            height_range=(180, 180),
            hair_color="brown",
            eye_color="brown",
            species="human",
            notable_accessories=["DL-44 blaster", "holster", "Corellian bloodstripe"],
            costume_variations=["smuggler outfit", "Hoth parka", "Endor trench coat", "carbonite block"]
        ),
        timeline=CharacterTimeline(
            original_era=True,
            sequel_era=True,
            standalone_era=True,  # Solo movie
            tv_series=["The Clone Wars"]
        ),
        first_meeting_context="Mos Eisley Cantina when hired by Luke and Obi-Wan",
        recognition_priority=8,
        confidence_threshold=0.75,
        canon_status="canon",
        notes="Initially skeptical of droids but develops respect for R2-D2's capabilities"
    )

    # Chewbacca - Loyal Wookiee co-pilot
    chewbacca = StarWarsCharacter(
        name="Chewbacca",
        aliases=["Chewie", "Chewbacca"],
        full_name="Chewbacca",
        titles=["Co-pilot"],
        faction=FactionAlignment.REBEL_ALLIANCE,
        species="Wookiee",
        homeworld="Kashyyyk",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.AFFECTIONATE_WHISTLES,
            secondary_emotions=[EmotionalResponse.PLAYFUL_TRILLS],
            sound_pattern="Gentle mechanical sounds mimicking Wookiee speech patterns",
            behavioral_notes="R2-D2 often tries to communicate in Wookiee-like sounds around Chewbacca",
            confidence_modifier=1.0
        ),
        trust_level=8,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Bandolier and utility belt",
            distinctive_features=["tall brown fur", "blue eyes", "bowcaster", "distinctive growl"],
            height_range=(228, 228),
            hair_color="brown",
            eye_color="blue",
            species="Wookiee",
            notable_accessories=["bowcaster", "bandolier", "tool pouch"],
            costume_variations=["standard fur", "Endor gear", "formal ceremony appearance"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            original_era=True,
            sequel_era=True,
            standalone_era=True
        ),
        first_meeting_context="Millennium Falcon in Mos Eisley docking bay",
        recognition_priority=7,
        confidence_threshold=0.70,
        canon_status="canon",
        notes="R2-D2 and Chewbacca have mutual respect despite language barriers"
    )

    # C-3PO - R2-D2's closest droid companion
    threepio = StarWarsCharacter(
        name="C-3PO",
        aliases=["Threepio", "3PO", "See-Threepio"],
        full_name="C-3PO",
        titles=["Protocol Droid"],
        faction=FactionAlignment.DROID,
        species="droid",
        homeworld="Tatooine",
        relationship_to_r2d2=RelationshipType.FELLOW_DROID,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.BINARY_PROFANITY,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES, EmotionalResponse.ANGRY_BUZZES],
            sound_pattern="Mix of exasperated electronic sounds and caring beeps",
            behavioral_notes="Constant bickering but deep loyalty; R2-D2 often shocked C-3PO for comic relief",
            confidence_modifier=1.3
        ),
        trust_level=10,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Golden protocol droid plating",
            distinctive_features=["golden metallic body", "yellow photoreceptors", "humanoid form"],
            height_range=(167, 167),
            hair_color=None,
            eye_color="yellow",
            species="droid",
            notable_accessories=["protocol droid plating", "restraining bolt socket"],
            costume_variations=["golden plating", "silver leg", "dismantled parts", "red arm", "Ewok deity decoration"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            original_era=True,
            sequel_era=True,
            standalone_era=True,
            tv_series=["The Clone Wars", "Rebels", "Resistance"]
        ),
        first_meeting_context="Built by Anakin Skywalker on Tatooine",
        recognition_priority=10,
        confidence_threshold=0.90,
        canon_status="canon",
        notes="R2-D2's oldest companion and translation partner. Their relationship is like an old married couple."
    )

    # Obi-Wan Kenobi - Trusted Jedi Master
    obiwan = StarWarsCharacter(
        name="Obi-Wan Kenobi",
        aliases=["Ben Kenobi", "Old Ben", "Obi-Wan"],
        full_name="Obi-Wan Kenobi",
        titles=["Jedi Master", "General"],
        faction=FactionAlignment.JEDI,
        species="human",
        homeworld="Stewjon",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.RESPECTFUL_ACKNOWLEDGMENT,
            secondary_emotions=[EmotionalResponse.EXCITED_BEEPS, EmotionalResponse.CAUTIOUS_CHIRPS],
            sound_pattern="Formal recognition beeps followed by warmer acknowledgment",
            behavioral_notes="R2-D2 shows deep respect but also familiarity from Clone Wars era",
            confidence_modifier=1.1
        ),
        trust_level=9,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Brown Jedi robes",
            distinctive_features=["reddish-brown hair/beard", "blue eyes", "Jedi lightsaber"],
            height_range=(182, 182),
            hair_color="reddish-brown",
            eye_color="blue",
            species="human",
            notable_accessories=["lightsaber", "Jedi robes", "utility belt"],
            costume_variations=["Jedi robes", "Clone Wars armor", "Tatooine hermit robes", "young Padawan appearance"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            original_era=True,
            tv_series=["The Clone Wars", "Rebels", "Obi-Wan Kenobi"]
        ),
        first_meeting_context="Naboo Royal Starship during Queen Amidala's escape",
        recognition_priority=9,
        confidence_threshold=0.80,
        canon_status="canon",
        notes="R2-D2 served alongside Obi-Wan during the Clone Wars. Can understand Binary."
    )

    # Darth Vader - Complex former ally turned enemy
    vader = StarWarsCharacter(
        name="Darth Vader",
        aliases=["Vader", "Lord Vader", "Anakin Skywalker"],
        full_name="Anakin Skywalker",
        titles=["Dark Lord of the Sith", "Jedi Knight (former)"],
        faction=FactionAlignment.SITH,
        species="human",
        homeworld="Tatooine",
        relationship_to_r2d2=RelationshipType.FORMER_ENEMY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.WORRIED_WARBLES,
            secondary_emotions=[EmotionalResponse.CAUTIOUS_CHIRPS, EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Conflicted mix of recognition and fear",
            behavioral_notes="R2-D2 shows conflicted emotions - fear of Vader but recognition of Anakin underneath",
            confidence_modifier=0.8
        ),
        trust_level=3,  # Complex - former 10, current enemy but still cares
        visual_descriptor=VisualDescriptor(
            primary_outfit="Black armor and cape",
            distinctive_features=["black mask", "mechanical breathing", "red lightsaber", "imposing height"],
            height_range=(203, 203),
            hair_color=None,
            eye_color="yellow/red",
            species="human",
            notable_accessories=["life support armor", "cape", "red lightsaber", "control panel"],
            costume_variations=["standard black armor", "meditation chamber", "damaged armor"]
        ),
        timeline=CharacterTimeline(
            original_era=True,
            standalone_era=True,  # Rogue One
            tv_series=["Rebels", "Obi-Wan Kenobi"]
        ),
        first_meeting_context="Originally met as Anakin Skywalker on Tatooine",
        recognition_priority=9,
        confidence_threshold=0.85,
        canon_status="canon",
        notes="R2-D2's most complex relationship - former closest friend Anakin now as Darth Vader"
    )

    # === PREQUEL TRILOGY CHARACTERS ===

    # Anakin Skywalker (young) - R2-D2's original closest friend
    anakin = StarWarsCharacter(
        name="Anakin Skywalker",
        aliases=["Ani", "Skywalker", "The Chosen One"],
        full_name="Anakin Skywalker",
        titles=["Jedi Knight", "General", "Podracer"],
        faction=FactionAlignment.JEDI,
        species="human",
        homeworld="Tatooine",
        relationship_to_r2d2=RelationshipType.CLOSE_FRIEND,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.EXCITED_BEEPS,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES, EmotionalResponse.PLAYFUL_TRILLS],
            sound_pattern="Enthusiastic beeps and whistles with mechanical laughter",
            behavioral_notes="R2-D2's strongest bond - complete trust and playful interaction",
            confidence_modifier=1.3
        ),
        trust_level=10,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Jedi robes",
            distinctive_features=["blonde hair", "blue eyes", "Padawan braid", "mechanical hand"],
            height_range=(185, 185),
            hair_color="blonde",
            eye_color="blue",
            species="human",
            notable_accessories=["lightsaber", "Jedi robes", "utility belt", "mechanical hand"],
            costume_variations=["slave boy clothes", "Padawan robes", "Jedi Knight robes", "dark side transition"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            tv_series=["The Clone Wars"]
        ),
        first_meeting_context="Watto's junkshop on Tatooine",
        recognition_priority=10,
        confidence_threshold=0.85,
        canon_status="canon",
        notes="R2-D2's original owner and closest friend. Strongest canonical relationship before fall to dark side."
    )

    # Padmé Amidala - Trusted leader and friend
    padme = StarWarsCharacter(
        name="Padmé Amidala",
        aliases=["Queen Amidala", "Senator Amidala", "Padmé"],
        full_name="Padmé Naberrie Amidala",
        titles=["Queen of Naboo", "Senator"],
        faction=FactionAlignment.GALACTIC_REPUBLIC,
        species="human",
        homeworld="Naboo",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.RESPECTFUL_ACKNOWLEDGMENT,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Formal but warm acknowledgment beeps",
            behavioral_notes="R2-D2 shows great respect for Padmé's leadership and kindness",
            confidence_modifier=1.0
        ),
        trust_level=9,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Elaborate royal gowns",
            distinctive_features=["brown hair in elaborate styles", "brown eyes", "royal makeup"],
            height_range=(165, 165),
            hair_color="brown",
            eye_color="brown",
            species="human",
            notable_accessories=["royal jewelry", "blaster", "comlink", "elaborate headdresses"],
            costume_variations=["royal gowns", "handmaiden disguise", "senator outfits", "travel clothes", "Geonosis arena outfit"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            tv_series=["The Clone Wars"]
        ),
        first_meeting_context="Naboo Royal Starship during escape from Trade Federation",
        recognition_priority=8,
        confidence_threshold=0.75,
        canon_status="canon",
        notes="R2-D2 served Padmé loyally during the Clone Wars and earlier conflicts"
    )

    # Qui-Gon Jinn - Respected Jedi Master
    quigon = StarWarsCharacter(
        name="Qui-Gon Jinn",
        aliases=["Qui-Gon", "Master Jinn"],
        full_name="Qui-Gon Jinn",
        titles=["Jedi Master"],
        faction=FactionAlignment.JEDI,
        species="human",
        homeworld="Coruscant",
        relationship_to_r2d2=RelationshipType.RESPECTED_LEADER,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.RESPECTFUL_ACKNOWLEDGMENT,
            secondary_emotions=[EmotionalResponse.CAUTIOUS_CHIRPS],
            sound_pattern="Formal acknowledgment beeps with undertones of respect",
            behavioral_notes="R2-D2 shows appropriate deference to Jedi authority",
            confidence_modifier=0.9
        ),
        trust_level=8,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Brown Jedi robes",
            distinctive_features=["long brown hair", "beard", "blue eyes", "Jedi lightsaber"],
            height_range=(193, 193),
            hair_color="brown",
            eye_color="blue",
            species="human",
            notable_accessories=["lightsaber", "Jedi robes", "utility belt", "comlink"],
            costume_variations=["standard Jedi robes", "Tatooine desert gear", "formal Jedi attire"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            tv_series=["The Clone Wars"]
        ),
        first_meeting_context="Naboo Royal Starship during Queen Amidala's escape",
        recognition_priority=7,
        confidence_threshold=0.70,
        canon_status="canon",
        notes="R2-D2's first interaction with a Jedi Master, establishing respect for Jedi authority"
    )

    # Mace Windu - Respected Jedi Council member
    mace = StarWarsCharacter(
        name="Mace Windu",
        aliases=["Master Windu", "Mace"],
        full_name="Mace Windu",
        titles=["Jedi Master", "Member of the Jedi Council", "General"],
        faction=FactionAlignment.JEDI,
        species="human",
        homeworld="Haruun Kal",
        relationship_to_r2d2=RelationshipType.RESPECTED_LEADER,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.RESPECTFUL_ACKNOWLEDGMENT,
            secondary_emotions=[EmotionalResponse.CAUTIOUS_CHIRPS],
            sound_pattern="Formal military-style acknowledgment beeps",
            behavioral_notes="R2-D2 shows formal respect for high-ranking Jedi authority",
            confidence_modifier=0.8
        ),
        trust_level=7,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Brown Jedi robes",
            distinctive_features=["bald head", "dark skin", "stern expression", "purple lightsaber"],
            height_range=(188, 188),
            hair_color=None,
            eye_color="brown",
            species="human",
            notable_accessories=["purple lightsaber", "Jedi robes", "utility belt"],
            costume_variations=["standard Jedi robes", "Clone Wars armor", "formal Council attire"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            tv_series=["The Clone Wars"]
        ),
        first_meeting_context="Jedi Temple during Anakin's evaluation",
        recognition_priority=6,
        confidence_threshold=0.70,
        canon_status="canon",
        notes="Limited direct interaction but represents Jedi authority R2-D2 respects"
    )

    # === SEQUEL TRILOGY CHARACTERS ===

    # Rey - New generation Jedi
    rey = StarWarsCharacter(
        name="Rey",
        aliases=["Rey Skywalker", "The Scavenger"],
        full_name="Rey Skywalker",
        titles=["Jedi", "Scavenger"],
        faction=FactionAlignment.RESISTANCE,
        species="human",
        homeworld="Jakku",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.CAUTIOUS_CHIRPS,
            secondary_emotions=[EmotionalResponse.EXCITED_BEEPS, EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Initial uncertainty followed by growing warmth",
            behavioral_notes="R2-D2 gradually warms to Rey as she proves herself worthy of the Skywalker legacy",
            confidence_modifier=1.0
        ),
        trust_level=8,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Scavenger wraps and tunic",
            distinctive_features=["brown hair in buns", "hazel eyes", "staff weapon", "lightsaber"],
            height_range=(170, 170),
            hair_color="brown",
            eye_color="hazel",
            species="human",
            notable_accessories=["quarterstaff", "lightsaber", "arm wraps", "scavenger gear"],
            costume_variations=["Jakku scavenger outfit", "Resistance fighter gear", "Jedi robes", "dark side vision"]
        ),
        timeline=CharacterTimeline(
            sequel_era=True
        ),
        first_meeting_context="Takodana when BB-8 introduces her to R2-D2",
        recognition_priority=8,
        confidence_threshold=0.75,
        canon_status="canon",
        notes="R2-D2 initially cautious but comes to accept Rey as worthy of the Skywalker legacy"
    )

    # Finn - Resistance hero and friend
    finn = StarWarsCharacter(
        name="Finn",
        aliases=["FN-2187", "Finn"],
        full_name="Finn",
        titles=["Stormtrooper (former)", "Resistance Fighter"],
        faction=FactionAlignment.RESISTANCE,
        species="human",
        homeworld="Unknown",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.CAUTIOUS_CHIRPS,
            secondary_emotions=[EmotionalResponse.EXCITED_BEEPS],
            sound_pattern="Careful acknowledgment with growing enthusiasm",
            behavioral_notes="R2-D2 initially wary due to Finn's stormtrooper background but quickly accepts him",
            confidence_modifier=0.9
        ),
        trust_level=7,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Resistance jacket",
            distinctive_features=["dark skin", "close-cropped hair", "brown eyes"],
            height_range=(175, 175),
            hair_color="black",
            eye_color="brown",
            species="human",
            notable_accessories=["blaster", "Resistance gear", "lightsaber (temporarily)"],
            costume_variations=["stormtrooper armor", "Poe's jacket", "Resistance uniform", "Canto Bight formal wear"]
        ),
        timeline=CharacterTimeline(
            sequel_era=True
        ),
        first_meeting_context="Resistance base after escaping First Order",
        recognition_priority=6,
        confidence_threshold=0.70,
        canon_status="canon",
        notes="Former stormtrooper who defected to join the Resistance"
    )

    # Poe Dameron - Resistance pilot
    poe = StarWarsCharacter(
        name="Poe Dameron",
        aliases=["Poe", "Black Leader"],
        full_name="Poe Dameron",
        titles=["Commander", "Pilot", "General"],
        faction=FactionAlignment.RESISTANCE,
        species="human",
        homeworld="Yavin 4",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.EXCITED_BEEPS,
            secondary_emotions=[EmotionalResponse.PLAYFUL_TRILLS],
            sound_pattern="Enthusiastic pilot-to-pilot acknowledgment",
            behavioral_notes="R2-D2 respects Poe's piloting skills and Resistance dedication",
            confidence_modifier=1.0
        ),
        trust_level=7,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Orange Resistance pilot suit",
            distinctive_features=["dark curly hair", "brown eyes", "pilot helmet", "jacket"],
            height_range=(175, 175),
            hair_color="brown",
            eye_color="brown",
            species="human",
            notable_accessories=["pilot helmet", "blaster", "flight suit", "jacket"],
            costume_variations=["X-wing pilot suit", "Resistance uniform", "casual jacket", "undercover disguise"]
        ),
        timeline=CharacterTimeline(
            sequel_era=True
        ),
        first_meeting_context="Resistance base during First Order conflict",
        recognition_priority=6,
        confidence_threshold=0.70,
        canon_status="canon",
        notes="Ace Resistance pilot whom R2-D2 respects for his skills"
    )

    # Kylo Ren - Complex enemy with family connections
    kylo = StarWarsCharacter(
        name="Kylo Ren",
        aliases=["Ben Solo", "Master of the Knights of Ren"],
        full_name="Ben Solo",
        titles=["Master of the Knights of Ren", "Supreme Leader"],
        faction=FactionAlignment.FIRST_ORDER,
        species="human",
        homeworld="Chandrila",
        relationship_to_r2d2=RelationshipType.FORMER_ENEMY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.WORRIED_WARBLES,
            secondary_emotions=[EmotionalResponse.CAUTIOUS_CHIRPS, EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Conflicted sounds of recognition and concern",
            behavioral_notes="R2-D2 recognizes Ben Solo underneath, showing conflicted emotions",
            confidence_modifier=0.8
        ),
        trust_level=4,  # Complex due to family connection
        visual_descriptor=VisualDescriptor(
            primary_outfit="Black robes and mask",
            distinctive_features=["long dark hair", "dark eyes", "red lightsaber", "scarred face"],
            height_range=(189, 189),
            hair_color="black",
            eye_color="brown",
            species="human",
            notable_accessories=["crossguard lightsaber", "mask", "black robes", "cape"],
            costume_variations=["masked appearance", "unmasked", "Supreme Leader attire", "redeemed Ben Solo"]
        ),
        timeline=CharacterTimeline(
            sequel_era=True
        ),
        first_meeting_context="Knew him as child Ben Solo through family connections",
        recognition_priority=7,
        confidence_threshold=0.75,
        canon_status="canon",
        notes="Son of Leia and Han - R2-D2 knew him as a child before his fall to the dark side"
    )

    # === TV SERIES CHARACTERS ===

    # Ahsoka Tano - Trusted Jedi ally
    ahsoka = StarWarsCharacter(
        name="Ahsoka Tano",
        aliases=["Snips", "Fulcrum", "Ahsoka"],
        full_name="Ahsoka Tano",
        titles=["Jedi Padawan (former)", "Togruta", "Rebel Agent"],
        faction=FactionAlignment.JEDI,
        species="Togruta",
        homeworld="Shili",
        relationship_to_r2d2=RelationshipType.TRUSTED_ALLY,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.EXCITED_BEEPS,
            secondary_emotions=[EmotionalResponse.AFFECTIONATE_WHISTLES, EmotionalResponse.PLAYFUL_TRILLS],
            sound_pattern="Warm, familiar acknowledgment beeps",
            behavioral_notes="Strong bond from Clone Wars era, R2-D2 shows genuine affection",
            confidence_modifier=1.1
        ),
        trust_level=9,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Blue and white Jedi attire",
            distinctive_features=["blue and white head-tails", "blue eyes", "Togruta markings", "twin lightsabers"],
            height_range=(170, 180),  # Grows throughout series
            hair_color=None,
            eye_color="blue",
            species="Togruta",
            notable_accessories=["twin lightsabers", "Jedi attire", "head-tail accessories"],
            costume_variations=["Padawan outfit", "Jedi attire", "civilian disguise", "Rebel agent gear", "white robes"]
        ),
        timeline=CharacterTimeline(
            prequel_era=True,
            tv_series=["The Clone Wars", "Rebels", "The Mandalorian", "Ahsoka"]
        ),
        first_meeting_context="Introduced by Anakin during Clone Wars",
        recognition_priority=8,
        confidence_threshold=0.80,
        canon_status="canon",
        notes="Close friend from Clone Wars era, trusted ally and former Jedi"
    )

    # BB-8 - Fellow Resistance droid
    bb8 = StarWarsCharacter(
        name="BB-8",
        aliases=["BB-8", "Beebee-Ate"],
        full_name="BB-8",
        titles=["Astromech Droid"],
        faction=FactionAlignment.RESISTANCE,
        species="droid",
        homeworld="Unknown",
        relationship_to_r2d2=RelationshipType.FELLOW_DROID,
        r2d2_reaction=R2D2Reaction(
            primary_emotion=EmotionalResponse.PLAYFUL_TRILLS,
            secondary_emotions=[EmotionalResponse.EXCITED_BEEPS, EmotionalResponse.AFFECTIONATE_WHISTLES],
            sound_pattern="Friendly droid-to-droid communication",
            behavioral_notes="Mutual respect between astromech droids, sharing technical information",
            confidence_modifier=1.0
        ),
        trust_level=8,
        visual_descriptor=VisualDescriptor(
            primary_outfit="Orange and white plating",
            distinctive_features=["spherical body", "orange and white coloring", "single photoreceptor"],
            height_range=(67, 67),
            hair_color=None,
            eye_color="blue",
            species="droid",
            notable_accessories=["astromech tools", "antenna", "various utility arms"],
            costume_variations=["standard orange/white", "battle-damaged", "disguised"]
        ),
        timeline=CharacterTimeline(
            sequel_era=True
        ),
        first_meeting_context="Resistance base during First Order conflict",
        recognition_priority=7,
        confidence_threshold=0.85,
        canon_status="canon",
        notes="Fellow astromech droid serving the Resistance"
    )

    # Add all characters to database
    characters = [luke, leia, han, chewbacca, threepio, obiwan, vader, anakin, padme,
                 quigon, mace, rey, finn, poe, kylo, ahsoka, bb8]

    for character in characters:
        character.last_updated = datetime.now().isoformat()
        db.add_character(character)

    return db


def create_reaction_sound_library():
    """Create detailed sound library for R2-D2 reactions"""
    sound_library = {
        EmotionalResponse.EXCITED_BEEPS: {
            "primary_sounds": ["ascending whistle", "rapid beeping", "enthusiastic chirps"],
            "duration": "2-4 seconds",
            "pitch": "high to very high",
            "pattern": "ascending then playful variations",
            "intensity": "high energy",
            "examples": ["Luke recognition", "successful mission completion", "C-3PO reunion"]
        },
        EmotionalResponse.WORRIED_WARBLES: {
            "primary_sounds": ["descending warbles", "anxious electronic sounds", "nervous chirping"],
            "duration": "3-5 seconds",
            "pitch": "medium with fluctuations",
            "pattern": "wavering uncertainty",
            "intensity": "medium with concern",
            "examples": ["Vader proximity", "dangerous situations", "unknown threats"]
        },
        EmotionalResponse.ANGRY_BUZZES: {
            "primary_sounds": ["harsh buzzing", "frustrated electronic raspberries", "indignant beeps"],
            "duration": "1-3 seconds",
            "pitch": "low to medium",
            "pattern": "sharp, staccato bursts",
            "intensity": "high frustration",
            "examples": ["C-3PO arguments", "ignored commands", "technical malfunctions"]
        },
        EmotionalResponse.CAUTIOUS_CHIRPS: {
            "primary_sounds": ["hesitant chirps", "questioning beeps", "uncertain warbles"],
            "duration": "2-3 seconds",
            "pitch": "medium",
            "pattern": "tentative, questioning",
            "intensity": "low to medium",
            "examples": ["meeting new people", "unfamiliar situations", "potential threats"]
        },
        EmotionalResponse.AFFECTIONATE_WHISTLES: {
            "primary_sounds": ["gentle whistles", "caring electronic sounds", "warm beeping"],
            "duration": "3-4 seconds",
            "pitch": "medium to high",
            "pattern": "smooth, melodic",
            "intensity": "gentle warmth",
            "examples": ["close friends", "family moments", "protective situations"]
        },
        EmotionalResponse.WARNING_ALARMS: {
            "primary_sounds": ["alarm beeps", "urgent whistles", "danger signals"],
            "duration": "1-2 seconds repeated",
            "pitch": "high, piercing",
            "pattern": "rapid, insistent repetition",
            "intensity": "high urgency",
            "examples": ["immediate danger", "security alerts", "emergency situations"]
        },
        EmotionalResponse.SURPRISED_SQUEAKS: {
            "primary_sounds": ["high-pitched squeaks", "startled beeps", "shock sounds"],
            "duration": "1-2 seconds",
            "pitch": "very high",
            "pattern": "sudden, sharp",
            "intensity": "brief high energy",
            "examples": ["unexpected events", "sudden appearances", "shocking revelations"]
        },
        EmotionalResponse.PLAYFUL_TRILLS: {
            "primary_sounds": ["musical trills", "mischievous beeping", "playful warbles"],
            "duration": "2-4 seconds",
            "pitch": "medium to high",
            "pattern": "musical, varying",
            "intensity": "lighthearted",
            "examples": ["pranks on C-3PO", "playful interactions", "humorous situations"]
        },
        EmotionalResponse.BINARY_PROFANITY: {
            "primary_sounds": ["harsh electronic sounds", "rapid angry beeping", "indignant buzzes"],
            "duration": "1-3 seconds",
            "pitch": "low to medium",
            "pattern": "rapid, harsh sequences",
            "intensity": "high frustration/anger",
            "examples": ["extreme frustration", "insults (in Binary)", "angry responses"]
        },
        EmotionalResponse.MECHANICAL_NEUTRAL: {
            "primary_sounds": ["standard acknowledgment beep", "neutral electronic tone"],
            "duration": "1 second",
            "pitch": "medium",
            "pattern": "simple, clear",
            "intensity": "neutral",
            "examples": ["unknown persons", "routine tasks", "professional interactions"]
        }
    }
    return sound_library


if __name__ == "__main__":
    # Create the database
    db = create_star_wars_character_database()

    # Export to JSON
    db.export_to_json("/home/rolo/r2ai/star_wars_character_database.json")

    # Print statistics
    stats = db.get_database_stats()
    print("Star Wars Character Database Statistics:")
    print(f"Total Characters: {stats['total_characters']}")
    print(f"Average Trust Level: {stats['average_trust_level']:.1f}")
    print(f"High Priority Characters: {stats['high_priority_count']}")
    print("\nFaction Distribution:")
    for faction, count in stats['faction_distribution'].items():
        print(f"  {faction}: {count}")
    print("\nRelationship Distribution:")
    for rel, count in stats['relationship_distribution'].items():
        print(f"  {rel}: {count}")

    # Create sound library
    sounds = create_reaction_sound_library()
    print(f"\nCreated sound library with {len(sounds)} emotion types")