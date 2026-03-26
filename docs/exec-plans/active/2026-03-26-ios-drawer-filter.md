# iOS Drawer Filter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Restore the same sidebar quick-filter affordance on iPhone and iPad that already exists on macOS. The target behavior is that the iOS drawer/sidebar exposes a visible filter field, applies the existing shared file-filtering logic as the user types, and remains compatible with the current compact iPhone and split-view iPad navigation shells.

## Progress

- [x] (2026-03-26T21:05Z) Confirmed the root cause: `ViewerShellView.sidebarContent` renders the filter field only inside `#if os(macOS)`, so iOS never shows the control even though it already uses the same shared `filteredFiles` logic.
- [x] (2026-03-26T21:13Z) Lifted the sidebar filter UI into the shared sidebar path, kept the macOS-only focus handling guarded, and added stable accessibility identifiers for the field and clear button.
- [x] (2026-03-26T21:13Z) Added a focused iPhone UI regression that opens the drawer, types into the filter, and asserts that the visible sidebar files narrow to the matching document.
- [x] (2026-03-26T21:58Z) Ran the narrow validation loop: the focused filter unit test passed, `python3 scripts/check_execplan.py` passed, `python3 scripts/knowledge/check_docs.py` passed, and a direct iOS simulator build passed; the local iPhone UITest runner and the existing iOS smoke wrapper both hit separate environment-side launch/capture issues after compile.

## Surprises & Discoveries

- Observation: the filtering behavior itself is already cross-platform because `filteredFiles` always delegates to `AppModel.filteredFiles(from:matching:)`; only the input UI is missing on iOS.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift` defines `sidebarFilterText` and `filteredFiles` outside platform guards, but wraps `sidebarFilterField` and its insertion in `#if os(macOS)`.

- Observation: the new iPhone UITest compiled successfully for iOS, but the local simulator refused to launch `Swift-Markdown-ViewerUITests.xctrunner`, so the new UI regression could not be executed end to end in this environment.
  Evidence: the focused `xcodebuild ... "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testiPhoneDrawerQuickFilterNarrowsSidebarFiles" test` run failed with `FBSOpenApplicationServiceErrorDomain Code=1` and `RequestDenied` while launching `com.matthewpaulmoore.Swift-Markdown-ViewerUITests.xctrunner`.

- Observation: the existing `./scripts/test-ui-ios --device iphone --smoke` wrapper still builds the app and boots the simulator, but the capture phase can exit with a generic `No such file or directory` before copying the harness artifacts.
  Evidence: the smoke run reported `** BUILD SUCCEEDED **` and completed `simctl bootstatus`, then exited with `NSPOSIXErrorDomain, code=2` and left `artifacts/checkpoints/shell-smoke-iphone/` empty.

## Decision Log

- Decision: keep a shared inline sidebar filter field instead of adding an iOS-only toolbar search affordance.
  Rationale: the drawer/sidebar is where the file list lives, the filtering logic already exists there, and one shared control avoids divergent platform behavior.
  Date/Author: 2026-03-26 / Codex

## Outcomes & Retrospective

The iOS sidebar now renders the same quick-filter affordance as macOS. `ViewerShellView` no longer hides the filter behind a macOS compile guard, the iOS field uses visible system styling with the existing shared `sidebarFilterText` binding, and the same shared `AppModel.filteredFiles(from:matching:)` logic now powers the drawer on iPhone and iPad as well as the macOS sidebar.

The implementation stayed intentionally small. Rather than inventing an iOS-only search surface, the change extends the existing sidebar control and preserves the macOS-specific keyboard focus behavior exactly where it already belongs. Stable accessibility identifiers were added so the drawer filter can be targeted by automation once the local iOS UITest runner issue is cleared.

## Context and Orientation

Relevant files:

- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/Harness/AccessibilityIDs.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerTests/Swift_Markdown_ViewerTests.swift`
- `docs/debug-contracts.md`

## Plan of Work

1. Move the sidebar filter field into the shared sidebar path while keeping macOS-only keyboard focus handling behind platform guards.
2. Add stable accessibility identifiers for the filter field so UI automation can find it on iOS.
3. Add a focused iOS UI regression that opens the drawer, types into the filter, and verifies the filtered file list.
4. Run the narrowest relevant test slice plus the required plan/docs checks.

## Concrete Steps

1. Refactor `ViewerShellView.sidebarFilterField` so it compiles on both platforms and uses platform-specific styling only where required.
2. Add new accessibility identifiers for the sidebar filter field and clear button, and document them in `docs/debug-contracts.md`.
3. Add a focused UI test that launches in iPhone mode, opens the file drawer, filters the workspace, and asserts the visible file list updates.
4. Run the targeted UI or unit validation slice, then `python3 scripts/check_execplan.py`, then `python3 scripts/knowledge/check_docs.py`.

## Validation and Acceptance

Acceptance requires:

- iPhone and iPad sidebar/drawer surfaces render a visible quick-filter control
- typing into the iOS filter updates the file list using the existing shared filter logic
- the filter field exposes stable accessibility identifiers suitable for UI automation
- focused regression coverage exists and passes when the local iOS UITest runner is healthy, plus `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`

## Idempotence and Recovery

The change is limited to the shared sidebar view, accessibility identifiers, and focused tests/docs. If the shared inline field causes an iOS layout regression, recovery is to keep the identifiers/tests and move the same `sidebarFilterText` binding into an alternate sidebar-local presentation without touching the filtering logic.

## Artifacts and Notes

Planned validation commands:

- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-ios-filter -destination "platform=iOS Simulator,name=iPhone 16" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testiPhoneDrawerQuickFilterNarrowsSidebarFiles" test`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

Validation completed:

- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-ios-filter -destination 'platform=iOS Simulator,id=32B9E37C-0C26-4514-9BBE-65718682A713' CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testiPhoneDrawerQuickFilterNarrowsSidebarFiles" test` failed in the environment while launching `Swift-Markdown-ViewerUITests.xctrunner` on the simulator.
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-filter-unit -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelFiltersFilesByQuickFilterQuery" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -sdk iphonesimulator -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-ios-filter-build CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= build`
- `./scripts/test-ui-ios --device iphone --smoke` built and booted the simulator but failed in the existing capture wrapper before artifacts were copied.
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

## Interfaces and Dependencies

No new dependencies are required. The change stays inside the existing SwiftUI shell and XCTest UI automation surfaces.
