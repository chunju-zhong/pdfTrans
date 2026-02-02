## Problem
A text block that only appears once (like "Figure 10: Alpha Evolve design system") is being incorrectly marked as non-body text.

## Root Cause
In the `_add_similar_blocks` method, when comparing text blocks within the same list (e.g., `top_blocks` vs `top_blocks`), each block is compared with every other block in the list, including itself. Since the similarity between a block and itself is 100%, it gets added to the `non_body_texts` set.

## Solution
Modify the `_add_similar_blocks` method to skip comparing a block with itself.

## Implementation Steps
1. Add a check in the `_add_similar_blocks` method to skip comparisons where:
   - `page1 == page2` and `block1.block_text == block2.block_text`
   - Or, more precisely, `page1 == page2` and `block1.block_no == block2.block_no`

2. Update the comparison logic to ensure we only compare different blocks, even when they're in the same list.

3. Test the fix with the example text block to ensure it's no longer incorrectly marked as non-body text.