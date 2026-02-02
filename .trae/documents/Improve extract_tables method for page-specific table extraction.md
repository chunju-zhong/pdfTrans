## Improve extract_tables method for page-specific table extraction

### Issues identified:
1. **Inefficient page height retrieval**: Currently iterates through all pages even when only specific pages are requested
2. **Lack of page number validation**: Doesn't check if requested pages are within valid range
3. **No duplicate page removal**: Could lead to redundant processing
4. **Inconsistent page number handling**: Different approach than extract_text method

### Improvement plan:
1. **Optimize page height retrieval**:
   - Only get heights for requested pages when pages parameter is specified
   - Use the same 1-based to 0-based conversion as extract_text

2. **Add page number validation**:
   - Validate that requested pages are within 1 to total_pages range
   - Log warnings for out-of-range pages
   - Remove invalid pages from processing

3. **Remove duplicate pages**:
   - Sort and deduplicate requested pages before processing
   - Ensure consistent handling with extract_text method

4. **Maintain backward compatibility**:
   - Keep the same method signature
   - Continue supporting None for all pages

5. **Add unit tests**:
   - Test with specific page ranges
   - Test with out-of-range pages
   - Test with duplicate pages

### Expected outcome:
- More efficient processing for large PDFs when extracting tables from specific pages
- Consistent page number handling across extract_tables and extract_text methods
- Better error handling for invalid page requests
- Maintain existing functionality while improving performance