# Async Cancelable Document Loading

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this change, document selection no longer blocks the app window while markdown file I/O and parsing run. The detail pane should show a visible loading indicator while the selected document is being prepared, and rapid adjacent navigation from the sidebar should cancel any in-flight document load before starting the next one. Keyboard-driven up/down movement should therefore feel responsive even when document parsing is expensive.

## Progress

- [x] (2026-03-23T20:22Z) Confirmed the current bottleneck: `AppModel.openFile(_:)` performs file reads and `MarkdownRenderer.blocks(from:)` synchronously on the main actor.
- [x] (2026-03-23T20:25Z) Moved document loading onto a cancelable background task, added request identity gating, and now cancel stale loads before new explicit or adjacent navigation requests start.
- [x] (2026-03-23T20:25Z) Updated the detail pane to show a visible loading overlay while document work is in flight without blocking sidebar interaction.
- [x] (2026-03-23T20:25Z) Ran the narrow unit slice successfully after moving document work off the main actor.
- [x] (2026-03-23T23:11Z) Removed accidental default `MainActor` isolation from `MarkdownRenderer` after renderer-sensitive validation surfaced host-test runtime traps in the async parsing path.

## Surprises & Discoveries

- Observation: the sidebar next/previous behavior already routes through one helper, so load cancellation can be centralized in `openFile(_:)`.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/AppModel.swift` sends arrow-key movement through `selectAdjacentFile(offset:)`, which already resolves a target path then calls `openFile(_:)`.

- Observation: the module’s default main-actor isolation was not just noisy for parser helpers; under host-based renderer tests it could escalate into an abort once parsing ran off the main actor.
  Evidence: the targeted selection-validation slice crashed in `Swift_Markdown_ViewerTests.testMarkdownRendererParsesMultipleBlockKinds()` until `MarkdownRenderer` itself was marked `nonisolated`.

## Decision Log

- Decision: keep `selectedPath` updating immediately when a new document is requested, but defer text/block replacement until the async load completes.
  Rationale: the sidebar selection should reflect the user’s intent instantly, while the detail pane can continue showing prior content with a loading overlay until the new content is ready.

- Decision: use explicit task cancellation and last-request identity checks instead of queueing loads.
  Rationale: adjacent keyboard navigation should prefer the latest requested document and stop wasting time on loads the user already moved past.

## Outcomes & Retrospective

`AppModel.openFile(_:)` no longer blocks the window while loading a document. Selection updates immediately, a background task reads and parses the markdown, and only the latest active request is applied. Starting a new adjacent navigation request cancels the in-flight task and prevents stale content from replacing the newer selection. The detail pane keeps rendering while work is in flight and shows a centered loading overlay so users can see that the selected document is still being prepared.

`MarkdownRenderer` is now explicitly nonisolated, so the async loader can continue parsing off the main actor without the earlier helper-isolation traps surfacing in targeted renderer validation. That keeps the document-loading path aligned with the repo’s longer-term Swift 6 isolation direction instead of leaving a known runtime hazard in place.

## Context and Orientation

Relevant files:

- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/AppModel.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerTests/Swift_Markdown_ViewerTests.swift`

## Plan of Work

1. Add cancelable document-load bookkeeping to `AppModel`.
2. Move file reading and markdown parsing into a detached task that returns a load result.
3. Surface an `isLoadingDocument` state to the detail UI and render a `ProgressView` overlay.
4. Extend narrow tests around adjacent selection and task-gating helpers.
5. Run targeted unit tests plus `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`.

## Concrete Steps

1. Replace synchronous `readFile`/`MarkdownRenderer.blocks` in `openFile(_:)` with a background loader result application path.
2. Cancel the active document task before any new explicit or adjacent open request.
3. Add a visible loading indicator to `ViewerShellView.detailContent`.
4. Add narrow tests that avoid the unstable app-hosted renderer teardown path where possible.

## Validation and Acceptance

Acceptance requires:

- selecting a document no longer blocks the UI thread during file read and parse work
- the detail pane shows a visible loading state while work is in flight
- rapid up/down navigation cancels stale loads and leaves the final selected document as the only applied result
- targeted unit tests pass
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass

## Idempotence and Recovery

This change is limited to in-process state management. If async loading regresses harness determinism, recovery is to disable cancellation or revert the async task path rather than changing workspace persistence or fixture contents.

## Artifacts and Notes

Expected validation command:

- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-async-loading -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" test`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

## Interfaces and Dependencies

No new external dependencies are required. The implementation uses Swift concurrency, existing workspace loading, and the current native SwiftUI shell.
