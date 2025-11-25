# FanqieQimaoDownloader - AI Coding Agent Instructions

## Project Overview
This is a novel downloader project for Chinese reading platforms **番茄小说 (Fanqie)** and **七猫小说 (Qimao)** using Rain API V3. The repository is currently in the **specification/planning phase** with reference documentation only.

### Current State
- **No implementation code yet** - only reference materials in `/reference/`
- API specifications are complete and ready for implementation
- Target: Build a downloader tool/library to fetch and save novels from these platforms

## Architecture & API Integration

### Rain API V3 Endpoints
Base URL: `http://v3.rain.ink/fanqie/` (Fanqie) or `http://v3.rain.ink/qimao/` (Qimao)  
API Key: `YOUR_API_KEY_HERE` (示例，需要用户自己配置)

**Core API Operations (type parameter):**
1. `type=1` - Search books (`&keywords={keyword}&page={page}`)
2. `type=2` - Get book details (`&bookid={bookId}`)
3. `type=3` - Get chapter list/TOC (`&bookid={bookId}`)
4. `type=4` - Get chapter content (`&itemid={itemId}`)

**Special Features:**
- AI audiobook mode: prefix search with `@` (e.g., `@禁神之下`)
- Real person audio: prefix search with `!` (e.g., `!禁神之下`)
- Audio voice selection via `tone_id` parameter (see `reference/FANQIE_RULES.md`)

### Data Flow Pattern
Search → Book Details → Chapter List → Chapter Content (iterate)

Key fields to extract:
- **Book**: `book_id`, `book_name`, `author`, `word_number`, `creation_status`, `last_chapter_title`
- **Chapter**: `item_id`, `title`, `volume_name`, `chapter_word_number`
- **Content**: Plain text or audio URL depending on mode

## Reference Files (Critical Reading)

### `reference/FANQIE_RULES.json`
Complete阅读3 (YueDu3) book source configuration with:
- JavaScript-based parsing rules for each API type
- Cover URL processing: `replaceCover()` function converts Fanqie URLs to `p6-novel.byteimg.com/origin` format
- Authentication flow using `fanqienovel.com` sessionid cookie
- Special handling for search result structures (check `search_tabs` vs `data` field)

### `reference/FANQIE_EXAMPLE.txt`
Full API response examples with:
- Complete JSON schemas for each endpoint
- JavaScript parsing code snippets (阅读3 compatible)
- Common edge cases (e.g., `search_tabs` can be null)

### `reference/FANQIE_RULES.md`
Human-readable API documentation covering:
- Parameter specifications
- Audio mode mechanics (8 = read, 32 = audio)
- Timestamp handling (Unix timestamps need `*1000` for JS Date)

### `reference/QIMAO_RULES.json`
Similar structure for Qimao platform with differences:
- Different field names: `original_title` vs `book_name`, `ptags` vs `tags`
- Requires `bid` storage during book info parsing (see `@put:{bid:id}`)
- Content endpoint needs both `id` and `chapterid` parameters

## Implementation Guidance

### When Building the Downloader
1. **Start with core API client**: Implement the 4 API types as separate methods
2. **Handle rate limiting**: Free tier limited to 200 chapters/day
3. **Parse responses carefully**: 
   - Check `message === 'SUCCESS'` on search results
   - Handle both `search_tabs[].data` and direct `data` array
   - Some fields use Unix timestamps (need conversion)

### Cover Image Processing
Always transform Fanqie cover URLs using this pattern:
```javascript
// Remove https:// prefix, replace domain with p6-novel.byteimg.com/origin
// Strip query params and tilde suffixes from path segments
```
See `replaceCover()` in `FANQIE_RULES.json` for reference implementation.

### Cookie Authentication (Optional Feature)
- Fanqie supports logged-in users via `sessionid` cookie from `fanqienovel.com`
- Required for accessing user bookshelf (`/api/bookshelf/multidetail`)
- Not mandatory for basic search/download functionality

### Output Formats to Consider
- Plain text files (one file per chapter or full book)
- EPUB generation (requires chapter metadata: title, volume, word count)
- Audio download support (extract audio URLs from type=4 with audio mode)

## Project-Specific Conventions

### Expected Tech Stack
Based on `.gitignore`:
- **Python** is the expected implementation language
- Standard Python project structure: `build/`, `dist/`, `*.egg-info/`
- Consider using `requests` for HTTP, `json` for parsing

### Key Design Decisions
1. **Why two platforms?** Both use same API provider (Rain API V3) with similar patterns
2. **Why阅读3 format?** Reference files are for popular Chinese novel reader app integration
3. **Rate limiting exists**: Build with exponential backoff and user warnings

### Testing Strategy
Use these validation points from `FANQIE_RULES.json`:
- Search checkpoint: `checkKeyWord: "转生三无猫娘，成神的我只想摸鱼"`
- Verify search returns expected book structure
- Test both normal and audio modes

## Common Pitfalls
- **Don't confuse `book_id` and `item_id`**: Former for books, latter for chapters
- **Search results vary**: Always check for `search_tabs` structure first
- **Time zones matter**: API uses UTC+8/UTC+12, adjust `timeFormatUTC` accordingly
- **Qimao requires bid persistence**: Store book ID when parsing info for chapter URL construction
