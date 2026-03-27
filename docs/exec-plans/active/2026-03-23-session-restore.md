# Resume Last Open Workspaces on Launch

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this change, quitting the macOS app with multiple folder-backed windows open should persist those window workspaces and restore them at the next normal launch. Each reopened window should restore its own folder and selected document, while harness-driven and UI-test launches must stay deterministic and skip state restoration.

## Progress

- [x] (2026-03-23T21:16Z) Added a `WorkspaceWindowSessionStore` that persists active window sessions and supplies claimed sessions to newly launched `WindowGroup` scenes.
- [x] (2026-03-23T21:16Z) Updated the app scene wiring so the first restored session claims the initial window and remaining saved sessions schedule additional macOS windows on launch.
- [x] (2026-03-23T21:16Z) Extended `AppModel` with `initialSession` restore inputs and `restorationSession` outputs so each window can restore and repersist its own folder plus selected file.
- [x] (2026-03-23T21:16Z) Fixed the temporary-directory path canonicalization bug that broke restored selections on macOS when `/var` and `/private/var` aliases disagreed.
- [x] (2026-03-23T21:16Z) Ran the narrow macOS unit slice successfully, including direct coverage for restored sessions and canonical relative workspace paths.
- [x] (2026-03-23T21:45Z) Stopped persisting session state during window disappearance so normal app quit no longer clears restore history and retriggers the empty-window folder prompt on next launch.
- [x] (2026-03-23T21:52Z) Added eager persistence on window-title changes so debugger-driven Xcode stop/start cycles keep the most recent workspace session even when normal app termination does not run.
- [x] (2026-03-23T22:24Z) Removed the startup `nil` session write from `WindowSceneRootView` and delayed scene-removal persistence so restored launches and normal quit no longer erase saved sessions before bootstrap or termination complete.
- [x] (2026-03-23T23:37Z) Updated the launch prompt policy so windows reopened from saved sessions no longer trigger the boot-time folder chooser, while explicit new windows still prompt normally.

## Surprises & Discoveries

- Observation: temporary test roots can enumerate file URLs under `/private/...` even when the chosen workspace root is stored under `/var/...`.
  Evidence: the first restore test failed with selected paths like `/privatealpha.md`, which came from `WorkspaceProvider.markdownFiles(in:)` doing a raw string replacement on mismatched canonical paths.

- Observation: persisting scene state only on phase changes leaves closed-window sessions behind during a long-running app session.
  Evidence: `WindowSceneRootView` previously removed a scene from memory on disappear, but `WorkspaceWindowSessionStore` did not persist that removal unless another later lifecycle event happened.

- Observation: persisting immediately on `onDisappear` is too aggressive for app termination because disappearing windows can run before the final quit-time persistence snapshot.
  Evidence: the app could launch into the folder picker even with prior session history because `removeActiveSession(for:)` eagerly overwrote the saved session list while the app was shutting down.

- Observation: Xcode’s Stop button can bypass normal quit-time persistence, so relying on app termination alone is not enough for development launches.
  Evidence: the restore flow still prompted for a folder on Xcode play/stop cycles until the session store started updating from visible workspace changes after bootstrap.

- Observation: restored scenes were still able to erase their own history during launch because `WindowSceneRootView.onAppear` persisted `model.restorationSession` before bootstrap had reloaded the workspace root.
  Evidence: `AppRootView` starts `model.bootstrap()` in a `.task`, so `model.restorationSession` is still `nil` at initial scene appearance even when `initialSession` is present.

- Observation: suppressing only the first launch scene is not enough once multi-window restoration is enabled, because additional restored windows also appear during startup and would still auto-open the chooser.
  Evidence: `WindowSceneRootView` calls its prompt check from every scene `onAppear`, and `WorkspaceWindowSessionStore.scheduleAdditionalWindows(openWindow:)` creates extra launch-time scenes for saved sessions.

## Decision Log

- Decision: persist lightweight workspace sessions in `UserDefaults` and reopen extra windows through `WindowGroup(for: String.self)`.
  Rationale: this matches the existing per-window scene model and avoids introducing a heavier document registry or platform-specific restoration framework.

- Decision: treat restoration as unavailable for harness, fixture, screenshot, and UI-test launches.
  Rationale: those launch modes need deterministic inputs and must not inherit prior interactive app state.

- Decision: canonicalize enumerated file paths with `resolvingSymlinksInPath().standardizedFileURL` before deriving relative markdown paths.
  Rationale: this is the smallest reliable fix for macOS temporary-directory aliasing without changing workspace semantics elsewhere.

## Outcomes & Retrospective

The app now resumes folder-backed macOS windows from the previous normal quit. Each restored scene claims its own saved workspace root and selected document, and additional saved sessions reopen as separate windows instead of collapsing into the first scene. The active-session store now persists on real session updates and removals, so closed windows stop being restored on later launches.

The main implementation risk turned out to be path identity rather than scene creation. macOS temp directories can surface through multiple equivalent path spellings, and the original relative-path derivation broke restored selections because it assumed raw string prefixes would match exactly. Canonicalizing both sides fixed the restore behavior and tightened workspace enumeration in general.

One follow-up adjustment was required after the first restore rollout: window disappearance during quit was clearing the saved session list before the next launch, which made the app think it had no history and prompt for a folder immediately. The fix was to keep in-memory removal behavior for closed windows but stop rewriting persistence during `onDisappear`, leaving the last valid saved session snapshot intact until a later explicit update or quit-time save.

Another follow-up was required for debugger-driven launches. Because `AppRootView` starts bootstrap in a `.task`, a restored or newly opened workspace may not be persisted yet if the user stops the app from Xcode before a normal quit path runs. Updating the session store on `windowTitle` changes makes workspace selection durable as soon as the folder and selected file become visible, which keeps Xcode play/stop behavior aligned with regular launches.

The final issue was lifecycle ordering. A restored scene was writing `nil` session state during `onAppear`, and normal quit could still clear in-memory sessions on `onDisappear` before the delayed termination snapshot happened. The fix was to stop writing session state on scene appearance and to delay removal persistence long enough for app termination to mark itself, while still allowing genuinely closed windows to fall out of the saved session list shortly afterward.

One more launch-semantics adjustment was needed after restore support landed. The startup folder chooser logic originally treated every non-harness scene after the first as a user-created window, which meant launch-restored secondary windows could still open `NSOpenPanel` during app boot. Moving that decision behind a small prompt policy keyed by "restored session vs. explicit new window" keeps relaunches quiet while preserving the desired prompt when the user actually creates a new empty window.

## Context and Orientation

Relevant files:

- `Free Markdown Viewer/Free Markdown Viewer/Free_Markdown_ViewerApp.swift`
- `Free Markdown Viewer/Free Markdown Viewer/App/Shell/WindowSceneRootView.swift`
- `Free Markdown Viewer/Free Markdown Viewer/App/Shared/AppModel.swift`
- `Free Markdown Viewer/Free Markdown Viewer/App/Shared/WorkspaceProvider.swift`
- `Free Markdown Viewer/Free Markdown Viewer/App/Shared/WorkspaceWindowSessionStore.swift`
- `Free Markdown Viewer/Free Markdown ViewerTests/Free_Markdown_ViewerTests.swift`

## Plan of Work

1. Introduce a window-session persistence store that survives normal app relaunches but stays disabled for harnessed launches.
2. Wire scene startup so restored sessions can claim the first window and reopen additional windows automatically.
3. Extend `AppModel` to restore the prior workspace root and selected file for each scene.
4. Add narrow tests for session restoration and the temporary-root path canonicalization regression.
5. Run targeted unit tests plus `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`.

## Concrete Steps

1. Persist `[WorkspaceWindowSession]` under a dedicated `UserDefaults` key.
2. Feed claimed sessions into `WindowSceneRootView` when a scene is constructed.
3. Publish `AppModel.restorationSession` so scene updates can repersist current state.
4. Canonicalize workspace-root and file paths before creating relative markdown paths.
5. Record the new behavior and validation evidence in repo control-plane docs.

## Validation and Acceptance

Acceptance requires:

- a normal macOS app relaunch reopens all previously open folder-backed windows
- each reopened window restores its own selected folder and document instead of sharing state
- harness and UI-test launches skip restoration
- restored selections survive temporary-directory path aliasing on macOS
- targeted unit tests pass
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass

## Idempotence and Recovery

The persistence format is a simple encoded array of lightweight session records. If restoration misbehaves, recovery is to clear the `workspaceWindowSessions` `UserDefaults` key or temporarily disable restoration gating while keeping the per-window scene ownership intact.

## Artifacts and Notes

Validation commands run:

- `xcodebuild -quiet -project "Free Markdown Viewer/Free Markdown Viewer.xcodeproj" -scheme "Free Markdown Viewer" -configuration Debug -derivedDataPath /tmp/free-markdown-viewer-session-restore-13 -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testWorkspaceProviderReturnsRelativePathsForTemporaryRoots" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" test`
- `xcodebuild -quiet -project "Free Markdown Viewer/Free Markdown Viewer.xcodeproj" -scheme "Free Markdown Viewer" -configuration Debug -derivedDataPath /tmp/free-markdown-viewer-session-restore-14 -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testIntegrationWorkspaceLoadsFixtureAndSnapshot" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testWorkspaceProviderReturnsRelativePathsForTemporaryRoots" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" test`
- `xcodebuild -quiet -project "Free Markdown Viewer/Free Markdown Viewer.xcodeproj" -scheme "Free Markdown Viewer" -configuration Debug -derivedDataPath /tmp/free-markdown-viewer-session-restore-15 -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testIntegrationWorkspaceLoadsFixtureAndSnapshot" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testWorkspaceProviderReturnsRelativePathsForTemporaryRoots" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" test`
- `xcodebuild -quiet -project "Free Markdown Viewer/Free Markdown Viewer.xcodeproj" -scheme "Free Markdown Viewer" -configuration Debug -derivedDataPath /tmp/free-markdown-viewer-session-restore-12 -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testWorkspaceProviderReturnsRelativePathsForTemporaryRoots" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAdjacentFilePathMovesSidebarSelection" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" test`
- `xcodebuild -quiet -project "Free Markdown Viewer/Free Markdown Viewer.xcodeproj" -scheme "Free Markdown Viewer" -configuration Debug -derivedDataPath /tmp/free-markdown-viewer-launch-prompt-fix -destination "platform=macOS,arch=arm64" CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAutomaticFolderPromptPolicySuppressesLaunchSceneOnly" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAutomaticFolderPromptPolicySuppressesRestoredScenes" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelAutoPromptsForFolderOnNormalMacLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelSkipsAutoPromptDuringUITestLaunch" "-only-testing:Free Markdown ViewerTests/Free_Markdown_ViewerTests/testAppModelRestoresInitialWorkspaceSession" test`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

## Interfaces and Dependencies

No new external dependencies are required. The implementation relies on existing SwiftUI window-scene APIs, `UserDefaults` for lightweight persistence, and the shared workspace-loading path.
