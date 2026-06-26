# Plan: CLI-WEB Feature Sync + SKILL.md Update

**Source**: /plan request + user confirmation
**Complexity**: Small

## Summary
Sync CLI (`pdftrans`) with WEB features: add Tibetan (bo) language support, add Qianfan (qianfan) translator to translate command, add combined output formats (pdf_docx/all), and update SKILL.md documentation to match.

## Work Units

| # | Unit | Files | Description |
|---|------|-------|-------------|
| 1 | CLI choices expansion | `cli.py` | Add `bo` to language choices (translate+glossary), `qianfan` to translator choices (translate), `pdf_docx`/`all` to format choices (translate) |
| 2 | Combined formats sync path | `services/translation_service.py`, `cli/translate_command.py` | Change `process_translation_sync` to return full file list; update handler to display all generated files for combined formats |
| 3 | SKILL.md documentation update | `SKILL.md` | Add bo language, qianfan translator + API config, combined formats, new usage examples, structure optimization |

## Dependencies
- Unit 1 and Unit 2 modify different parts of `cli.py` (lines 135-149 vs line 158) — git auto-merge will handle cleanly
- Unit 3 has zero code dependencies

## E2E Test Recipe
1. Run `pdftrans translate --help` — verify bo in language choices, qianfan in translator choices, pdf_docx/all in format choices
2. Run `pdftrans glossary --help` — verify bo in language choices
3. Run `pytest tests/test_cli.py -v` — all tests pass
4. For combined formats: `pdftrans translate test.pdf -f pdf_docx` and `-f all` should not crash
