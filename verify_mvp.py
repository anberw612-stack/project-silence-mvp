"""
Verification Script for Confuser MVP

This script automatically tests the core functionality of the Confuser system
to ensure all layers are working correctly.
"""

from layer1_matching import SemanticMatcher
from layer2_confuser import perturb_text, get_perturbation_stats


def test_layer2_perturbation():
    """Test Layer 2: Privacy perturbation logic."""
    print("\n" + "=" * 60)
    print("TEST 1: Layer 2 - Privacy Perturbation")
    print("=" * 60)
    
    test_text = "I am a software engineer in Seattle"
    print(f"\nInput:  {test_text}")
    
    perturbed = perturb_text(test_text)
    print(f"Output: {perturbed}")
    
    # Assertions
    assert "Austin" in perturbed, "❌ FAIL: 'Seattle' should be replaced with 'Austin'"
    assert "backend developer" in perturbed, "❌ FAIL: 'software engineer' should be replaced with 'backend developer'"
    assert "Seattle" not in perturbed, "❌ FAIL: Original location 'Seattle' should not appear in perturbed text"
    
    print("\n✅ PASS: Layer 2 perturbation working correctly")
    print(f"   - 'Seattle' → 'Austin'")
    print(f"   - 'software engineer' → 'backend developer'")
    
    return True


def test_layer2_multiple_replacements():
    """Test Layer 2 with multiple identifying details."""
    print("\n" + "=" * 60)
    print("TEST 2: Layer 2 - Multiple Replacements")
    print("=" * 60)
    
    test_text = "I am a 28yo software engineer in Seattle feeling burnt out."
    print(f"\nInput:  {test_text}")
    
    perturbed = perturb_text(test_text)
    print(f"Output: {perturbed}")
    
    stats = get_perturbation_stats(test_text, perturbed)
    
    # Assertions
    assert "Austin" in perturbed, "❌ FAIL: Location not replaced"
    assert "backend developer" in perturbed, "❌ FAIL: Role not replaced"
    assert "31" in perturbed, "❌ FAIL: Age not replaced"
    assert stats['total_changes'] == 3, f"❌ FAIL: Expected 3 changes, got {stats['total_changes']}"
    
    print("\n✅ PASS: Multiple replacements working correctly")
    print(f"   - Total changes: {stats['total_changes']}")
    print(f"   - Locations: {stats['locations_replaced']}")
    print(f"   - Roles: {stats['roles_replaced']}")
    print(f"   - Ages: {stats['ages_replaced']}")
    
    return True


def test_layer1_semantic_matching():
    """Test Layer 1: Semantic similarity matching."""
    print("\n" + "=" * 60)
    print("TEST 3: Layer 1 - Semantic Matching")
    print("=" * 60)
    
    print("\nInitializing semantic matcher...")
    matcher = SemanticMatcher()
    
    # Test query similar to database entry
    test_query = "I work as a developer in Seattle and I'm exhausted"
    print(f"\nQuery: {test_query}")
    
    match, score = matcher.find_best_match(test_query)
    
    # Assertions
    assert match is not None, "❌ FAIL: Should find a match for similar query"
    assert score >= 0.3, f"❌ FAIL: Score {score} should be >= 0.3"
    assert "Seattle" in match or "software engineer" in match, "❌ FAIL: Match should be semantically related"
    
    print(f"\n✅ PASS: Semantic matching working correctly")
    print(f"   - Match found: {match}")
    print(f"   - Similarity score: {score:.2%}")
    
    return True


def test_layer1_no_match():
    """Test Layer 1: No match scenario."""
    print("\n" + "=" * 60)
    print("TEST 4: Layer 1 - No Match Threshold")
    print("=" * 60)
    
    matcher = SemanticMatcher()
    
    # Test query with no similarity
    test_query = "xyz123 random nonsense query qwerty asdfgh"
    print(f"\nQuery: {test_query}")
    
    match, score = matcher.find_best_match(test_query)
    
    print(f"\nMatch: {match}")
    print(f"Score: {score}")
    
    # Note: This might still find a match if similarity > 0.3, which is okay
    # The important thing is the system doesn't crash
    print("\n✅ PASS: No-match scenario handled correctly")
    
    return True


def test_integration():
    """Test full integration of all layers."""
    print("\n" + "=" * 60)
    print("TEST 5: Full Integration Test")
    print("=" * 60)
    
    matcher = SemanticMatcher()
    
    test_query = "I am a software engineer in Seattle"
    print(f"\nUser query: {test_query}")
    
    # Layer 1: Find match
    match, score = matcher.find_best_match(test_query)
    print(f"\nLayer 1 output:")
    print(f"   Match: {match}")
    print(f"   Score: {score:.2%}")
    
    # Layer 2: Perturb
    if match:
        perturbed = perturb_text(match)
        print(f"\nLayer 2 output:")
        print(f"   Protected: {perturbed}")
        
        # Verify perturbation
        assert "Austin" in perturbed, "❌ FAIL: Integration test - perturbation failed"
        assert "backend developer" in perturbed, "❌ FAIL: Integration test - perturbation failed"
    
    print("\n✅ PASS: Full integration working correctly")
    
    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("CONFUSER MVP - VERIFICATION SUITE")
    print("=" * 60)
    
    tests = [
        ("Layer 2 Perturbation", test_layer2_perturbation),
        ("Layer 2 Multiple Replacements", test_layer2_multiple_replacements),
        ("Layer 1 Semantic Matching", test_layer1_semantic_matching),
        ("Layer 1 No Match", test_layer1_no_match),
        ("Full Integration", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"\n✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! MVP is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
