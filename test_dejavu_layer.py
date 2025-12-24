"""
Test script to verify the "Context First" Two-Step Retrieval Logic.

Core Philosophy: Trust the Metadata (ABC/Batch) first. Rely on Semantic Scores second.

STEP 1 - VIP CHECK (Metadata Priority):
    IF source_id matches match_batch_id -> BYPASS all score filters, return immediately.

STEP 2 - SEMANTIC FALLBACK (Strict Scoring for External Data):
    - Layer 1 (Precision): score > 0.85
    - Layer 2 (Resonance): 0.75 < score <= 0.85
    - Layer 3 (Déjà vu):   0.635 < score <= 0.75
    - Discard if score <= 0.635 (QNF)

Summary: Internal data (ABC met) is ALWAYS shown. External data only shown if score > 0.635.
"""


def test_context_first_retrieval():
    """
    Test the "Context First" two-step retrieval logic with mock data.
    Simulates the bucketization logic without requiring the full model.
    """

    # Simulate deduplicated items with scores and source_ids
    test_items = [
        # EXTERNAL DATA (different batch)
        {'id': 1, 'query': 'External high score', 'score': 0.90, 'source_id': 'batch_OTHER'},      # Should pass (Precision)
        {'id': 2, 'query': 'External mid score', 'score': 0.80, 'source_id': 'batch_OTHER'},       # Should pass (Resonance)
        {'id': 3, 'query': 'External low-mid score', 'score': 0.70, 'source_id': 'batch_OTHER'},   # Should pass (Déjà vu)
        {'id': 4, 'query': 'External below threshold', 'score': 0.60, 'source_id': 'batch_OTHER'}, # Should be DROPPED (QNF)

        # INTERNAL DATA (matching batch) - Should ALL pass regardless of score
        {'id': 5, 'query': 'Internal high score', 'score': 0.90, 'source_id': 'batch_MATCH'},      # VIP -> Precision label
        {'id': 6, 'query': 'Internal mid score', 'score': 0.78, 'source_id': 'batch_MATCH'},       # VIP -> Resonance label
        {'id': 7, 'query': 'Internal low score', 'score': 0.50, 'source_id': 'batch_MATCH'},       # VIP -> Déjà vu label (BYPASSES 0.635 threshold!)
        {'id': 8, 'query': 'Internal very low', 'score': 0.30, 'source_id': 'batch_MATCH'},        # VIP -> Déjà vu label (BYPASSES 0.635 threshold!)
    ]

    # The batch_id we're trying to match (current query's context)
    match_batch_id = 'batch_MATCH'

    # Apply the "Context First" two-step logic
    internal_matches = []  # VIP matches (Step 1)
    external_matches = []  # Semantic fallback candidates (Step 2)

    # ===================================================================
    # STEP 1: VIP CHECK (Metadata Priority)
    # ===================================================================
    for item in test_items:
        score = item['score']
        item_source_id = item.get('source_id')

        if match_batch_id is not None and item_source_id == match_batch_id:
            # INTERNAL MATCH: Bypass score filters, always include
            item['is_internal'] = True
            # Assign semantic label based on score (for display purposes)
            if score > 0.85:
                item['layer'] = 'Precision'
            elif score > 0.75:
                item['layer'] = 'Resonance'
            else:
                item['layer'] = 'Déjà vu'
            internal_matches.append(item)
        else:
            # No metadata match, proceed to Step 2
            item['is_internal'] = False
            external_matches.append(item)

    # ===================================================================
    # STEP 2: SEMANTIC FALLBACK (Strict Scoring for External Data)
    # ===================================================================
    precision = []
    resonance = []
    dejavu = []
    dropped = []

    for item in external_matches:
        score = item['score']

        # Layer 1 (Precision): score > 0.85
        if score > 0.85:
            item['layer'] = 'Precision'
            precision.append(item)
        # Layer 2 (Resonance): 0.75 < score <= 0.85
        elif score > 0.75:
            item['layer'] = 'Resonance'
            resonance.append(item)
        # Layer 3 (Déjà vu): 0.635 < score <= 0.75
        elif score > 0.635:
            item['layer'] = 'Déjà vu'
            dejavu.append(item)
        # QNF: score <= 0.635 -> discard
        else:
            item['layer'] = 'DROPPED (QNF - below threshold)'
            dropped.append(item)

    # Print results
    print("=" * 70)
    print("'CONTEXT FIRST' TWO-STEP RETRIEVAL TEST RESULTS")
    print("=" * 70)
    print(f"Match Batch ID: {match_batch_id}")
    print()

    print("=" * 70)
    print("STEP 1: VIP CHECK (Internal Matches - Score filters BYPASSED)")
    print("=" * 70)
    for item in internal_matches:
        print(f"   ✅ ID {item['id']}: Score {item['score']:.3f} | Layer: {item['layer']} | Source: {item['source_id']}")
    if not internal_matches:
        print("   (none)")

    print()
    print("=" * 70)
    print("STEP 2: SEMANTIC FALLBACK (External Data - Strict Scoring)")
    print("=" * 70)

    print("\n✅ PRECISION LAYER (> 0.85):")
    for item in precision:
        print(f"   ID {item['id']}: Score {item['score']:.3f} | Source: {item['source_id']}")
    if not precision:
        print("   (none)")

    print("\n✅ RESONANCE LAYER (0.75 < score <= 0.85):")
    for item in resonance:
        print(f"   ID {item['id']}: Score {item['score']:.3f} | Source: {item['source_id']}")
    if not resonance:
        print("   (none)")

    print("\n✅ DÉJÀ VU LAYER (0.635 < score <= 0.75):")
    for item in dejavu:
        print(f"   ID {item['id']}: Score {item['score']:.3f} | Source: {item['source_id']}")
    if not dejavu:
        print("   (none)")

    print("\n❌ DROPPED (QNF - score <= 0.635):")
    for item in dropped:
        print(f"   ID {item['id']}: Score {item['score']:.3f} | Source: {item['source_id']}")
    if not dropped:
        print("   (none)")

    print("\n" + "=" * 70)
    print("TEST VALIDATION")
    print("=" * 70)

    test_passed = True

    # -------------------------------------------------------------------------
    # Test Case 1: Internal data with LOW score (0.50) -> Should be INCLUDED (VIP bypass)
    # This is the KEY difference from the old logic!
    # -------------------------------------------------------------------------
    item7_in_internal = any(item['id'] == 7 for item in internal_matches)
    if item7_in_internal:
        print("✅ TEST 1 PASSED: Internal + Score 0.50 -> VIP BYPASS (included as Déjà vu)")
    else:
        print("❌ TEST 1 FAILED: Internal + Score 0.50 should bypass filters and be included")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 2: Internal data with VERY LOW score (0.30) -> Should be INCLUDED (VIP bypass)
    # -------------------------------------------------------------------------
    item8_in_internal = any(item['id'] == 8 for item in internal_matches)
    if item8_in_internal:
        print("✅ TEST 2 PASSED: Internal + Score 0.30 -> VIP BYPASS (included as Déjà vu)")
    else:
        print("❌ TEST 2 FAILED: Internal + Score 0.30 should bypass filters and be included")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 3: External data below threshold (0.60) -> Should be DROPPED
    # -------------------------------------------------------------------------
    item4_dropped = any(item['id'] == 4 for item in dropped)
    if item4_dropped:
        print("✅ TEST 3 PASSED: External + Score 0.60 -> DROPPED (QNF)")
    else:
        print("❌ TEST 3 FAILED: External + Score 0.60 should be dropped")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 4: External data in Déjà vu range (0.70) -> Should be INCLUDED
    # -------------------------------------------------------------------------
    item3_in_dejavu = any(item['id'] == 3 for item in dejavu)
    if item3_in_dejavu:
        print("✅ TEST 4 PASSED: External + Score 0.70 -> Included as Déjà vu")
    else:
        print("❌ TEST 4 FAILED: External + Score 0.70 should be in Déjà vu layer")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 5: External high score (0.90) -> Should be in Precision
    # -------------------------------------------------------------------------
    item1_in_precision = any(item['id'] == 1 for item in precision)
    if item1_in_precision:
        print("✅ TEST 5 PASSED: External + Score 0.90 -> Included as Precision")
    else:
        print("❌ TEST 5 FAILED: External + Score 0.90 should be in Precision layer")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 6: Internal high score -> Should have Precision label
    # -------------------------------------------------------------------------
    item5 = next((item for item in internal_matches if item['id'] == 5), None)
    if item5 and item5['layer'] == 'Precision':
        print("✅ TEST 6 PASSED: Internal + Score 0.90 -> Label is 'Precision'")
    else:
        print("❌ TEST 6 FAILED: Internal + Score 0.90 should have 'Precision' label")
        test_passed = False

    # -------------------------------------------------------------------------
    # Test Case 7: All internal items should have is_internal=True
    # -------------------------------------------------------------------------
    all_internal_flagged = all(item.get('is_internal') == True for item in internal_matches)
    if all_internal_flagged:
        print("✅ TEST 7 PASSED: All internal matches have is_internal=True")
    else:
        print("❌ TEST 7 FAILED: Internal matches should have is_internal=True flag")
        test_passed = False

    print("\n" + "=" * 70)
    if test_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("💥 SOME TESTS FAILED!")
    print("=" * 70)

    return test_passed


if __name__ == "__main__":
    test_context_first_retrieval()
