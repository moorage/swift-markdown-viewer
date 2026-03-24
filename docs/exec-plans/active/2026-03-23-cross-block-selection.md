# Cross-Block Document Selection

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this change, users can select and copy text across the entire visible document instead of being limited to individual rendered blocks. The implementation should prioritize the lowest-risk, most maintainable path; for this slice that means exposing the document as one native selectable text surface while still showing rendered markdown semantics instead of raw source.

## Progress

- [x] (2026-03-23T20:28Z) Confirmed the current limitation: document content is rendered as many separate SwiftUI `Text` views, so selection stops at block boundaries.
- [x] (2026-03-23T20:29Z) Proved the full-document selection path by replacing the block stack with one native selectable text surface, then confirmed that a raw-markdown backing regressed rendered output.
- [x] (2026-03-23T23:05Z) Switched the selectable surface to block-derived rendered text so users keep cross-block selection without losing heading/list/code presentation.
- [x] (2026-03-23T23:05Z) Preserved loading overlay and accessibility identifiers after the detail-pane swap and added a narrow regression test for the rendered selectable formatter.
- [x] (2026-03-23T23:11Z) Reran the targeted validation slice successfully after opting `MarkdownRenderer` out of accidental default `MainActor` isolation exposed during renderer-sensitive tests.

## Surprises & Discoveries

- Observation: `.textSelection(.enabled)` on the current `VStack` of block views does not create a unified selection region across child blocks.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift` wraps separate `MarkdownBlockView` instances in a `ScrollView`, which still yields per-block selection behavior.

- Observation: the raw-markdown fallback technically fixes selection, but it breaks the core viewer expectation because users stop seeing rendered markdown.
  Evidence: `ViewerShellView.detailContent` was wired to `model.documentText`, which shows source markers like `#`, list fences, and code fences instead of the parsed block presentation the app previously rendered.

## Decision Log

- Decision: use one native selectable text view backed by block-derived rendered text instead of raw markdown source or the old many-view block stack.
  Rationale: a single native text surface is still the lowest-risk route to cross-block selection, but feeding it rendered block text preserves the viewer’s core UX and avoids exposing markdown syntax directly.

- Decision: explicitly opt `MarkdownRenderer` out of the repo’s default `MainActor` isolation while validating this slice.
  Rationale: the selectable surface depends on async-loaded `documentBlocks`, and targeted renderer tests surfaced runtime traps from parser helper types inheriting `MainActor` isolation even though the renderer is intended to be pure background-safe logic.

## Outcomes & Retrospective

The detail pane now uses one native selectable text view rather than many block-local SwiftUI text views. Users can drag-select and copy across the full document, but they still see rendered markdown semantics because the selectable surface is populated from parsed blocks with heading/list/code styling instead of raw source. The existing async loading overlay remains visible while documents load, so the selection fix does not regress the non-blocking navigation work. While validating the change, `MarkdownRenderer` was also made explicitly nonisolated so the same parsed blocks remain safe to build off the main actor.

## Context and Orientation

Relevant files:

- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Platform/`

## Plan of Work

1. Add a platform-native selectable text view wrapper.
2. Replace the detail pane’s block renderer with that wrapper bound to rendered document blocks rather than raw markdown text.
3. Keep loading overlay, scrolling, and accessibility identifiers intact.
4. Run the existing narrow validation slice plus docs checks.

## Concrete Steps

1. Create a representable wrapper for `NSTextView` on macOS and `UITextView` on iOS.
2. Configure it for read-only but selectable behavior and block-derived rendered text styling.
3. Integrate it into `ViewerShellView.detailContent`.
4. Update plan/docs notes and rerun targeted validation.

## Validation and Acceptance

Acceptance requires:

- users can select and copy text across the whole document without block boundaries stopping selection
- rendered markdown remains visible instead of raw source syntax replacing it
- document loading overlay still appears while async loads are in flight
- existing targeted validation remains green
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass

## Idempotence and Recovery

The change is confined to the detail-pane view layer. If the native text view regresses layout or accessibility, recovery is to revert the detail-pane integration without touching the async loading model.

## Artifacts and Notes

Targeted validation command:

- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-selection-fix -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testSelectableDocumentFormatterUsesRenderedDocumentText" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testMarkdownRendererParsesMultipleBlockKinds" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" test`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

## Interfaces and Dependencies

No new external dependencies are required. The implementation uses AppKit/UIKit text views behind SwiftUI representable wrappers.
