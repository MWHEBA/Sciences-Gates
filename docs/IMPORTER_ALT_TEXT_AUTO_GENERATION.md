# WordPress Importer: Alt Text Auto-Generation

## Overview

The WordPress importer now automatically generates fallback alt text for images when WordPress provides empty or whitespace-only alt text values. This ensures better SEO scores out-of-the-box while still preserving manually written alt text from WordPress when available.

## Implementation

### Location
`apps/importer/services/content_mapper.py` - `ContentMapper.map_data()`

### Behavior

#### 1. Real Alt Text is Preserved
When WordPress provides actual alt text content:
- **Action**: Use the WordPress alt text exactly as provided
- **Confidence**: `high`
- **Example**: 
  ```python
  WordPress alt: "شعار جامعة مالايا - University of Malaya Logo"
  → Django form_initial: "شعار جامعة مالايا - University of Malaya Logo"
  → Confidence: "high"
  ```

#### 2. Empty Alt Text Triggers Auto-Generation
When WordPress provides empty or whitespace-only alt text:
- **Action**: Generate simple fallback based on entity name
- **Confidence**: `generated` (not `high`)
- **Logo**: `شعار {entity_name}`
- **Main Image**: `{entity_name}`
- **Featured Image**: `{entity_name}`

**Examples:**
```python
# Logo
WordPress alt: "" (empty)
Entity name: "جامعة مالايا الماليزية"
→ Generated: "شعار جامعة مالايا الماليزية"
→ Confidence: "generated"

# Main Image
WordPress alt: "   " (whitespace)
Entity name: "معهد التدريب الماليزي"
→ Generated: "معهد التدريب الماليزي"
→ Confidence: "generated"
```

#### 3. Empty Entity Name → No Generation
When entity name is empty:
- **Action**: Leave alt text empty
- **Confidence**: `none`

### Confidence Levels

The system uses a confidence tracking system to distinguish between different data sources:

| Confidence | Meaning | Use Case |
|------------|---------|----------|
| `high` | Real data from WordPress | Manually written alt text in WordPress |
| `generated` | Auto-generated fallback | Empty alt text from WordPress → auto-generated |
| `medium` | Transformed/split data | Split admission requirements |
| `none` | Missing data | No value available |

**Important**: `generated` confidence indicates the alt text is a simple fallback, not manually optimized SEO content. The editor can (and should) improve it later.

## Content Types

Auto-generation works across all content types:
- **University**: logo_alt, main_image_alt
- **Institute**: logo_alt, main_image_alt
- **Major**: main_image_alt
- **Article**: featured_image_alt

## Editor Workflow

The auto-generated alt text serves as a baseline:

1. **Import**: Content imported with auto-generated alt text
2. **Review**: Editor opens the edit page
3. **Improve**: Editor can enhance the auto-generated alt text with more descriptive SEO-optimized text
4. **SEO Score**: Model checker still warns if dedicated fields are empty (encourages manual improvement)

## Testing

Comprehensive test coverage in `apps/importer/tests.py`:

### Test Cases
1. ✅ Empty alt text → generates fallback
2. ✅ Real alt text → preserved exactly
3. ✅ Whitespace-only → treated as empty
4. ✅ Empty entity name → no generation
5. ✅ Mixed scenario (logo real, main empty)
6. ✅ All content types (university, institute, major)
7. ✅ Confidence levels correct

**All tests pass: 7/7 ✅**

## Example Import Flow

### Before (Old Behavior)
```
WordPress: logo_alt = "" (empty)
↓
Django: logo_alt = "" (empty)
Confidence: "none"
SEO Score: FAIL (missing alt text)
```

### After (New Behavior)
```
WordPress: logo_alt = "" (empty)
↓
Django: logo_alt = "شعار جامعة مالايا" (auto-generated)
Confidence: "generated"
SEO Score: WARNING (can be improved)
```

### With Real Alt Text (Unchanged)
```
WordPress: logo_alt = "Official University Logo with UM emblem"
↓
Django: logo_alt = "Official University Logo with UM emblem" (preserved)
Confidence: "high"
SEO Score: PASS ✅
```

## Benefits

1. **Better SEO Out-of-the-Box**: Auto-generated alt text prevents complete failures
2. **Preserves Manual Work**: Real alt text from WordPress is never overwritten
3. **Clear Confidence Tracking**: System knows difference between real and generated content
4. **Editor-Friendly**: Provides baseline that can be improved
5. **Accessibility**: Basic accessibility maintained even when WordPress lacks alt text

## Limitations

Auto-generated alt text is simple and generic:
- Does not describe image content in detail
- Not optimized for SEO keywords
- Should be improved manually for best results

The `generated` confidence level signals this limitation to the system.

## Future Improvements

Potential enhancements:
1. AI-powered image description generation
2. Keyword integration from focus_keyword field
3. Template-based generation (e.g., "Campus of {name} in {city}")
4. Confidence-based UI hints (show yellow badge for generated fields)

## Related Files

- `apps/importer/services/content_mapper.py` - Main implementation
- `apps/importer/services/image_downloader.py` - Image download with alt text
- `apps/importer/tests.py` - Test coverage
- `apps/seo/services/model_checks.py` - Model checker (still warns on empty DB fields)
- `templates/universities/detail.html` - Template with proper alt field usage

## See Also

- [SEO Alt Text Requirements](./SEO_ALT_TEXT_REQUIREMENTS.md)
- [Importer Architecture](./IMPORTER_ARCHITECTURE.md)
