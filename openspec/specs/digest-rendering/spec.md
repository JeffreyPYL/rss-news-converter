# Digest Rendering Specification

## Purpose

Turns a digest — grouped stories across topics — into the reader-facing document formats this project delivers.

## Requirements

### Requirement: Single combined output per run
One run SHALL produce one EPUB covering every topic that has qualifying stories in that run, not a separate document per topic.

#### Scenario: A run with stories in three topics produces one EPUB
- **WHEN** a run has qualifying stories in the Canada, Tech, and Global topics
- **THEN** exactly one EPUB is produced containing sections for all three topics

### Requirement: Images are retained in rendered output
Article images present in the extracted content SHALL be included in the rendered EPUB.

#### Scenario: An article with an image renders with that image visible
- **WHEN** a story entry's extracted article includes an image
- **THEN** the rendered EPUB displays that image within the corresponding story entry

### Requirement: Obsidian-compatible rendering
The same digest content SHALL also be renderable as an Obsidian-flavored Markdown note, in addition to the EPUB.

#### Scenario: The same run's content is available in both formats
- **WHEN** a run completes
- **THEN** both an EPUB and an Obsidian-flavored Markdown note are produced from the same underlying digest content

### Requirement: Navigable index
The rendered output SHALL include an index listing every story across all topics, and every story SHALL include a link back to that index — so a reader can jump between stories without scrolling through the whole document. The concrete link mechanism MAY differ by format (in-document anchors for the EPUB, Obsidian's heading-link syntax for the Markdown note).

#### Scenario: The EPUB index links to every story
- **WHEN** a run's EPUB is rendered
- **THEN** the EPUB includes an index page whose links resolve to each story's position in its topic chapter

#### Scenario: Every story in the EPUB links back to the index
- **WHEN** a reader reaches the end of a story's content in the EPUB
- **THEN** a link back to the index page is present immediately after it

#### Scenario: The Obsidian note has equivalent navigation
- **WHEN** a run's Obsidian note is rendered
- **THEN** the note includes an index section linking to every story's heading, and every story includes a link back to that index section
