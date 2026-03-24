# Window-Scoped Workspaces for New macOS Windows

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this change, each macOS window owns its own workspace selection instead of sharing a single process-wide folder. Creating an explicit new window should prompt for a folder so users can open a different workspace without overwriting the one already visible in another window, but normal app startup should not immediately show the chooser. Harness-driven launches and existing fixture-based automation must keep their current deterministic behavior.

## Progress

- [x] (2026-03-23T20:04Z) Confirmed the current bug source: `Swift_Markdown_ViewerApp` owns one `@StateObject AppModel`, so every `WindowGroup` scene instance shares the same workspace and navigation state.
- [x] (2026-03-23T20:13Z) Moved `AppModel` ownership into a per-window `WindowSceneRootView` and routed `Open Folder…` through a focused-scene action so the active window handles its own folder changes.
- [x] (2026-03-23T20:13Z) Added one-shot macOS startup prompting for windows launched without an explicit harness workspace source, while leaving harness and UI-test launch paths gated off.
- [x] (2026-03-23T20:13Z) Added targeted unit coverage for auto-prompt gating, ran the narrow unit slice successfully, and captured the existing macOS UI-test bootstrap crash as a validation gap.
- [x] (2026-03-23T23:37Z) Refined the macOS prompt policy so launch-created scenes, including restored windows, suppress the folder chooser while later explicit new windows still auto-prompt.
- [x] (2026-03-24T01:37Z) Fixed a bootstrap race where a newly selected folder could be overwritten by the window's initial workspace load, added fixture-backed alpha/beta workspaces, and covered the per-window isolation path with focused unit tests plus the existing single-window open-folder UI test.
- [x] (2026-03-24T02:20Z) Added a centered empty-workspace detail state with an "Open Another Folder" CTA and covered it with focused unit and macOS UI tests.

## Surprises & Discoveries

- Observation: the shared-folder behavior is architectural, not a bug inside `AppModel`.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/Swift_Markdown_ViewerApp.swift` creates one `@StateObject private var model` and injects it into every `WindowGroup` content instance.

- Observation: the existing macOS `Open Folder…` command already bypasses `NSOpenPanel` in UI-test mode.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/Swift_Markdown_ViewerApp.swift` checks `launchOptions.uiTestMode` and calls `model.openFolder(at:)` with `uiTestOpenFolderURL`.

- Observation: app-hosted renderer paths are still unstable in XCTest and can abort before deeper per-window integration assertions complete.
  Evidence: `~/Library/Logs/DiagnosticReports/Swift Markdown Viewer-2026-03-23-130930.ips` crashes in `MarkdownRenderer.BlockBuilder.__deallocating_deinit` during `AppModel.openFolder(at:)`, and the existing macOS UI test runner exits early before establishing the automation connection.

- Observation: the remaining "same folder in every window" behavior came from a race inside one window, not from scene ownership after the earlier refactor.
  Evidence: `AppModel.bootstrap()` could still apply the initial fixture/restored workspace after `openFolder(at:)` had already loaded a different folder, so the later bootstrap load replaced the user's newer selection.

- Observation: the empty-workspace state needs its own UI rather than rendering the placeholder text through the selectable document surface.
  Evidence: when a folder contains no `.md` files, the product expectation is a centered recovery affordance, not a document-like paragraph pinned to the top-left content area.

## Decision Log

- Decision: keep `AppModel` as the window-owned state container and fix scene ownership instead of introducing a global workspace registry.
  Rationale: the bug is that scenes share one model instance; moving model creation into a per-window root is the smallest change that restores expected document-window behavior.

- Decision: gate the auto-open-folder prompt behind launch-option heuristics so harnessed launches stay deterministic.
  Rationale: smoke tests and snapshot capture rely on explicit fixture roots and must not trigger modal UI during startup.

- Decision: treat the first launch scene and any scene that claims a restored session as non-interactive startup surfaces that must not auto-open the folder chooser.
  Rationale: startup-created windows are not user-requested "new window" actions, so prompting there is noisy and regresses relaunch behavior.

- Decision: treat the first successful workspace load in a window as authoritative and skip any later bootstrap default load for that window.
  Rationale: explicit folder selection is newer user intent than fixture/bootstrap defaults, so the initial async load must not clobber it.

## Outcomes & Retrospective

The code change now matches the requested window semantics on macOS. Each `WindowGroup` scene gets its own `AppModel`, `Open Folder…` targets the focused scene instead of a shared singleton, and explicit new windows without a claimed startup/restored session schedule a one-shot open-folder prompt on first appearance. Normal startup and restored launches no longer show the chooser immediately. Harness-style launches remain deterministic because the auto-prompt predicate disables itself when fixture roots, UI-test mode, snapshot output paths, or harness command directories are present.

Validation is now split between deterministic model coverage and the narrower passing macOS UI slice. The focused unit tests cover repeated UI-test folder arguments, the explicit-selection-vs-bootstrap race, and two independent window-owned models keeping different fixture folders/files after one window opens a new workspace. The single-window macOS UI `Open Folder…` path also passes. A true two-window XCUITest remains unreliable in this environment, so direct UI automation proof of simultaneous windows is still a residual gap even though the underlying bug is now covered and fixed.

## Context and Orientation

The relevant code lives in:

- `Swift Markdown Viewer/Swift Markdown Viewer/Swift_Markdown_ViewerApp.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/ContentView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/AppRootView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/AppModel.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerTests/Swift_Markdown_ViewerTests.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests.swift`

The current app-level `@StateObject` causes every macOS window to share the same `AppModel`. New-window behavior should remain macOS-specific; iPhone and iPad do not create independent top-level windows in this app flow.

## Plan of Work

1. Replace app-level model ownership with a per-window scene root that creates its own `AppModel`.
2. Expose an `Open Folder…` action from the focused window so the menu command affects only the active scene.
3. Add one-shot auto-prompt logic for macOS windows that launch without an explicit fixture root or harness command mode.
4. Extend narrow tests to cover the launch gating and workspace isolation behavior.
5. Run targeted unit tests, then `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`.

## Concrete Steps

1. Add a scene root view that owns `@StateObject private var model = AppModel(...)`.
2. Route the macOS command group through a focused window action instead of referencing a single app-global model.
3. Add a launch-behavior predicate on `AppModel` for whether startup should auto-prompt.
4. Add unit tests for that predicate and for two models selecting different folders independently.
5. Update this plan and `.agents/DOCUMENTATION.md`, then run validation.

## Validation and Acceptance

Acceptance requires all of the following:

- Opening a second macOS window no longer changes the first window's sidebar, title, or selected file.
- A newly created macOS window prompts for a folder automatically unless the app was launched in a harness-driven mode with an explicit fixture root or UI-test override.
- Existing `Open Folder…` menu behavior still works for the active window.
- Targeted unit tests pass.
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass after plan/doc updates.

## Idempotence and Recovery

This change is UI-state-only and should be safe to rerun. If the auto-prompt logic misfires during harness runs, revert by disabling the launch predicate rather than changing the workspace provider fallback behavior. Test workspaces should remain temporary directories under the system temp root.

## Artifacts and Notes

Expected validation commands:

- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-window-workspaces -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelsMaintainIndependentWorkspaceSelections" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-launch-prompt-fix -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAutomaticFolderPromptPolicySuppressesLaunchSceneOnly" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAutomaticFolderPromptPolicySuppressesRestoredScenes" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-multiwindow-unit-final -destination "platform=macOS,arch=arm64" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testLaunchOptionsParseMultipleUITestOpenFolders" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testOpenFolderSelectionWinsOverPendingBootstrapLoad" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testWindowScopedModelsKeepDifferentFoldersAfterOpeningNewWorkspace" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testIntegrationWorkspaceLoadsFixtureAndSnapshot" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-openfolder-ui-final -destination "platform=macOS,arch=arm64" "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testOpenFolderCommandUpdatesSidebarAndTitle" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-empty-state-unit -destination "platform=macOS,arch=arm64" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testEmptyWorkspaceShowsNoMarkdownFilesMessage" "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testWorkspaceProviderUsesChosenFolderWithoutFixtureFallback" test`
- `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-empty-state-ui-2 -destination "platform=macOS,arch=arm64" "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testOpenFolderCommandUpdatesSidebarAndTitle" "-only-testing:Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests/testEmptyWorkspaceShowsCenteredOpenFolderCallToAction" test`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

## Interfaces and Dependencies

No new external dependencies are required. The implementation depends on:

- SwiftUI scene/window lifecycle on macOS
- `NSOpenPanel` for folder selection
- existing `HarnessLaunchOptions` gating so harness/UI tests remain deterministic
