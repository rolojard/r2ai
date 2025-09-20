"""
Basic System Test for R2-D2 Star Wars Character Recognition
==========================================================

Simple test to validate the system components work together correctly.
"""

from star_wars_character_database_schema import *
from datetime import datetime


def test_character_creation():
    """Test basic character creation and schema validation"""
    print("Testing character creation...")

    # Create a simple test character
    test_character = StarWarsCharacter(
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
        )
    )

    print(f"✓ Successfully created character: {test_character.name}")
    print(f"  Faction: {test_character.faction.value}")
    print(f"  Relationship: {test_character.relationship_to_r2d2.value}")
    print(f"  Primary Reaction: {test_character.r2d2_reaction.primary_emotion.value}")
    print(f"  Trust Level: {test_character.trust_level}")

    return test_character


def test_database_operations():
    """Test database creation and operations"""
    print("\nTesting database operations...")

    db = CharacterDatabase()

    # Create test character
    test_char = test_character_creation()

    # Add to database
    db.add_character(test_char)
    print(f"✓ Added character to database")

    # Test retrieval
    retrieved = db.get_character("Luke Skywalker")
    if retrieved:
        print(f"✓ Successfully retrieved character: {retrieved.name}")
    else:
        print("✗ Failed to retrieve character")

    # Test faction filtering
    jedi_chars = db.get_characters_by_faction(FactionAlignment.JEDI)
    print(f"✓ Found {len(jedi_chars)} Jedi characters")

    # Test relationship filtering
    friends = db.get_characters_by_relationship(RelationshipType.CLOSE_FRIEND)
    print(f"✓ Found {len(friends)} close friends")

    # Test statistics
    stats = db.get_database_stats()
    print(f"✓ Database contains {stats['total_characters']} characters")

    return db


def test_validation():
    """Test character data validation"""
    print("\nTesting validation...")

    test_char = test_character_creation()
    issues = validate_character_data(test_char)

    if issues:
        print(f"✗ Validation issues found: {issues}")
    else:
        print("✓ Character data passes validation")

    return len(issues) == 0


def test_sound_library():
    """Test sound library creation"""
    print("\nTesting sound library...")

    try:
        from r2d2_reaction_system import R2D2ReactionEngine

        engine = R2D2ReactionEngine()
        print(f"✓ Created R2D2 reaction engine successfully")

        # Test sound library
        sound_lib = engine.sound_library
        print(f"✓ Sound library contains {len(sound_lib)} emotion types")

        # Test a specific emotion
        excited_sounds = sound_lib.get(EmotionalResponse.EXCITED_BEEPS)
        if excited_sounds:
            print(f"✓ Found excited beeps configuration")

        return True
    except Exception as e:
        print(f"✗ Sound library creation failed: {e}")
        return False


def test_image_dataset_manager():
    """Test image dataset manager"""
    print("\nTesting image dataset manager...")

    try:
        from image_dataset_recommendations import StarWarsImageDatasetManager

        manager = StarWarsImageDatasetManager()
        stats = manager.generate_dataset_statistics()

        print(f"✓ Dataset manager created successfully")
        print(f"  Total characters: {stats['total_characters']}")
        print(f"  Recommended images: {stats['total_recommended_images']:,}")
        print(f"  Estimated storage: {stats['estimated_storage_gb']:.1f} GB")

        return True
    except Exception as e:
        print(f"✗ Image dataset manager test failed: {e}")
        return False


def test_technical_integration():
    """Test technical integration specifications"""
    print("\nTesting technical integration...")

    try:
        from technical_integration_specifications import TechnicalIntegrationManager, HardwareProfile, ProcessingMode

        manager = TechnicalIntegrationManager()

        # Test deployment guide generation
        guide = manager.generate_deployment_guide(
            HardwareProfile.RASPBERRY_PI,
            ProcessingMode.REAL_TIME
        )

        print(f"✓ Technical integration manager created successfully")
        print(f"  Target FPS: {guide['deployment_configuration']['estimated_performance']['target_fps']}")
        print(f"  Hardware: {guide['hardware_requirements']['cpu']}")

        return True
    except Exception as e:
        print(f"✗ Technical integration test failed: {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive system test"""
    print("=" * 60)
    print("R2-D2 Star Wars Character Recognition System Test")
    print("=" * 60)

    tests = [
        ("Character Schema", test_character_creation),
        ("Database Operations", test_database_operations),
        ("Data Validation", test_validation),
        ("Sound Library", test_sound_library),
        ("Image Dataset Manager", test_image_dataset_manager),
        ("Technical Integration", test_technical_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result or result is None:  # None means no explicit return value (success)
                passed += 1
                print(f"\n✓ {test_name}: PASSED")
            else:
                print(f"\n✗ {test_name}: FAILED")
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)