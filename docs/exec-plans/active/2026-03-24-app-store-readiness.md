# App Store Readiness Without Icon Work

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Prepare the repository for the largest possible slice of App Store submission work that can be completed locally without App Store Connect credentials and without app-icon production. The target outcome is a codebase that is materially closer to a free App Store release on macOS, iPhone, and iPad: the app should expose a real customer-facing folder-opening flow on iPhone and iPad, declare submission-safe metadata where the Xcode project can do so, carry a privacy manifest, provide a repeatable release/archive command surface, and include repository-owned drafts for the support/legal website pages that App Store Connect will expect.

The app should remain free. There is no monetization or StoreKit work in scope. The website base is assumed to be `https://www.matthewpaulmoore.com/`, and this workstream should leave the user with concrete URLs to publish plus draft copy/templates to adapt before submission.

## Progress

- [x] (2026-03-24T08:02Z) Audited the live project, docs, tests, and release settings to identify the current submission blockers excluding icons.
- [x] (2026-03-24T08:09Z) Confirmed the largest product gap: macOS has a real folder chooser, but iPhone and iPad currently expose no equivalent folder-import flow and instead fall back to embedded fixtures.
- [x] (2026-03-24T08:17Z) Collected current external references for the Apple standard EULA and for starter privacy-policy / terms generators to include in the website/legal notes.
- [x] (2026-03-24T08:25Z) Implemented a real iPhone/iPad folder-import action in `WindowSceneRootView`, surfaced the action in the iOS top bar, and threaded workspace restoration through bookmark-backed session state.
- [x] (2026-03-24T08:29Z) Added submission-facing project metadata, a privacy manifest, release/archive scripting, and repository-owned App Store / support / privacy / terms draft docs rooted at the planned website URLs.
- [x] (2026-03-24T08:32Z) Revalidated the repo with `./scripts/test-unit`, an iOS simulator build, `python3 scripts/check_execplan.py`, and `python3 scripts/knowledge/check_docs.py`.
- [x] (2026-03-24T08:38Z) Broadened workspace discovery to common Markdown extensions, added an App Store export helper plus App Review notes draft, and reran unit/docs validation.
- [x] (2026-03-25T08:40Z) Generated the app icon set from `tmp/best 2.png`, added release-completion and App Store metadata docs, and kept the repo validation green.
- [x] (2026-03-25T09:35Z) Added a polished `Fixtures/app-store/` screenshot pack, a repeatable `scripts/capture-app-store-screenshots` flow, and generated usable iPhone and iPad candidate screenshots plus harness snapshots under `artifacts/app-store-screenshots/`.
- [x] (2026-03-25T09:35Z) Improved compact iPhone navigation so launch-selected documents open into the reader instead of staying stuck on the sidebar list, then tightened the compact top bar so capture output remains readable.
- [x] (2026-03-25T16:12Z) Routed code-block-only documents through the structured renderer, removed iPad back/forward labels, fixed macOS capture timing, hardened the iOS screenshot script against hanging `simctl` commands, and regenerated fresh iPad/macOS screenshot artifacts.
- [x] (2026-03-25T16:14Z) Added an explicit macOS startup icon install from the bundled `AppIcon.icns` resource so debug builds show the generated app icon in the Dock instead of the generic placeholder.

## Surprises & Discoveries

- Observation: the app is materially less submission-ready on iPhone and iPad than on macOS because the only real user-triggered workspace picker is macOS `NSOpenPanel`.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/WindowSceneRootView.swift` wires `openFolder()` only for `os(macOS)` and returns `nil` for the non-macOS `openFolderAction`.

- Observation: the current project uses generated Info.plists and has only a thin layer of submission-facing metadata configured.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj/project.pbxproj` contains deployment targets, bundle identifiers, and generated scene/launch keys, but no document-type declarations, no app category, no export-compliance key, and no explicit display-name/legal metadata.

- Observation: the app icon catalog structure exists, but the catalog currently contains no image payloads.
  Evidence: `Swift Markdown Viewer/Swift Markdown Viewer/Assets.xcassets/AppIcon.appiconset` currently contains only `Contents.json`. Icon work is intentionally out of scope for this plan.

- Observation: the project currently has no privacy manifest file at all.
  Evidence: a repository search for `PrivacyInfo.xcprivacy` returned no matches under `Swift Markdown Viewer/`.

- Observation: App Store submission still requires website-hosted operational/legal pages even for a free app with no analytics or account system.
  Evidence: the support URL and privacy policy URL live outside the Xcode project and must be supplied in App Store Connect. The Apple standard EULA page also remains a viable default when no custom EULA is provided.

- Observation: security-scoped bookmark creation and resolution are not configured identically across Apple platforms.
  Evidence: the first iOS simulator build failed because `.withSecurityScope` is unavailable in iOS bookmark creation and resolution calls, so the helper needed platform-conditional bookmark options even though `startAccessingSecurityScopedResource()` still exists on iOS.

- Observation: the internal macOS harness screenshot writer still does not produce App Store-usable output in this environment, even though the state/perf snapshots are correct.
  Evidence: generated macOS screenshots under `artifacts/app-store-screenshots/macos/` show mostly blank or black output while the paired `*.state.json` files report the expected selected file and visible blocks.

- Observation: compact iPhone launches initially stayed on the file list even when a specific file was preselected, which made the first pass of iPhone screenshots unusable.
  Evidence: the first captured iPhone screenshots under `artifacts/app-store-screenshots/iphone/` showed only the file list until the compact iPhone shell path was changed to swap between sidebar and detail explicitly.

- Observation: the original iPad screenshot path was also being undermined by a poisoned preferred simulator and by `simctl terminate` / `simctl uninstall` hanging indefinitely on that device.
  Evidence: direct subprocess probes against the preferred `iPad (A16)` simulator timed out on `xcrun simctl terminate` and `xcrun simctl uninstall`, while switching the preferred iPad destination and avoiding those calls allowed the capture flow to complete and refresh the PNGs.

- Observation: the generated macOS app bundle already contained the expected icon resources, but debug launches could still present a generic Dock icon.
  Evidence: the built app at `artifacts/DerivedData/Build/Products/Debug/Swift Markdown Viewer.app` contained both `Contents/Resources/AppIcon.icns` and `CFBundleIconName = AppIcon`, which points to runtime icon presentation rather than missing build assets.

## Decision Log

- Decision: prioritize product-complete iPhone/iPad file access over lower-value cosmetic release metadata.
  Rationale: a free Markdown viewer that cannot open a user-selected folder on iPhone/iPad is not meaningfully submission-ready even if the plist keys are polished.
  Date/Author: 2026-03-24 / Codex

- Decision: use the Apple standard EULA by default instead of introducing a custom EULA in this workstream.
  Rationale: the app is simple, free, local-first, and currently has no service-specific business terms that justify a custom EULA. The Apple standard EULA is the lowest-risk starting point.
  Date/Author: 2026-03-24 / Codex

- Decision: recommend website URLs under stable app and legal paths rooted at `https://www.matthewpaulmoore.com/`.
  Rationale: stable paths make it easier to reuse the same URLs in App Store Connect, inside the app, and in future release docs.
  Date/Author: 2026-03-24 / Codex

- Decision: add repository-owned website/legal draft content even though publication happens outside this repo.
  Rationale: the repo can still own the source text, URL map, and review checklist so App Store prep does not depend on memory or ad hoc notes.
  Date/Author: 2026-03-24 / Codex

- Decision: use platform-conditional bookmark options for workspace restoration, with security-scoped bookmark options on macOS and plain bookmark options on iOS.
  Rationale: the app still needs bookmark-backed restoration state on both platforms, but the iOS SDK rejects the macOS-specific `.withSecurityScope` bookmark options at compile time.
  Date/Author: 2026-03-24 / Codex

- Decision: add a repository-owned screenshot fixture set plus a one-command capture script instead of relying on ad hoc simulator browsing during release week.
  Rationale: repeatable screenshot inputs reduce last-minute App Store prep churn and create concrete artifacts the user can review before uploading.
  Date/Author: 2026-03-25 / Codex

- Decision: implement a dedicated compact iPhone reading flow that switches between the sidebar and detail content explicitly.
  Rationale: `NavigationSplitView` plus button-based sidebar rows left iPhone launches stranded on the file list, while an explicit compact swap fixes both real UX and screenshot capture quality without disturbing iPad/macOS layouts.
  Date/Author: 2026-03-25 / Codex

- Decision: delay harness screenshot writes slightly after the model reports ready, and prefer a healthy iPad simulator over a poisoned one for repeatable App Store capture.
  Rationale: macOS screenshots were being captured while the loading overlay was still visible, and the previously preferred iPad simulator repeatedly wedged on `simctl` lifecycle calls; both issues were capture-environment problems rather than renderer correctness problems.
  Date/Author: 2026-03-25 / Codex

- Decision: explicitly install the bundled macOS app icon at launch in addition to relying on the asset catalog and Info.plist metadata.
  Rationale: the bundle resources were correct, but an explicit `NSApplication.shared.applicationIconImage` assignment gives debug builds a deterministic Dock icon even when LaunchServices or the app cache lags behind the latest generated icon assets.
  Date/Author: 2026-03-25 / Codex

## Outcomes & Retrospective

This workstream materially improved real submission readiness without touching icons or App Store Connect. The app now exposes an actual folder-open workflow on iPhone and iPad, uses bookmark-backed workspace session state instead of raw paths alone, carries a privacy manifest, includes App Store-safe plist metadata, and ships with repository-owned drafts for the public support/privacy/terms pages that App Store Connect will need.

The highest-leverage product fix was not release metadata but replacing the iOS fixture-only posture with a real folder importer. That change moves the app closer to something a real App Store user can actually operate on-device. The supporting persistence work also keeps the restoration model aligned with sandboxed document access rather than assuming stable raw file paths.

The main implementation wrinkle was bookmark portability. macOS and iOS do not accept the same bookmark option set, so the helper had to split bookmark creation/resolution options by platform while keeping the higher-level restoration model shared.

The remaining submission work is now mostly external: live website publication, App Store Connect metadata entry, signing/team configuration, final review of the generated screenshot candidates, and the actual archive/upload flow using a real Apple Developer team.

One more incremental improvement landed after the first validation pass: the workspace scanner now accepts common Markdown extensions beyond `.md`, the release tooling now covers both archive and export steps with repo-owned documentation for App Review notes, and the repo now owns a polished screenshot fixture set plus repeatable capture output. The screenshot pipeline now generates upload-usable iPhone, iPad, and macOS images in this environment after the harness capture timing fix and iPad simulator fallback.

## Context and Orientation

The highest-impact product code lives in:

- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/WindowSceneRootView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/AppRootView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shell/ViewerShellView.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/AppModel.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/WorkspaceProvider.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/WorkspaceWindowSessionStore.swift`
- `Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj/project.pbxproj`

The supporting repository-owned release docs should live under `docs/` and the shell-first release helpers should live under `scripts/`.

Recommended website URLs for this app:

- `https://www.matthewpaulmoore.com/apps/swift-markdown-viewer`
- `https://www.matthewpaulmoore.com/apps/swift-markdown-viewer/support`
- `https://www.matthewpaulmoore.com/legal/privacy`
- `https://www.matthewpaulmoore.com/legal/terms`

The default-license path is Apple’s standard EULA:

- `https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`

Starter legal-template sources to adapt carefully, not copy blindly:

- `https://termly.io/products/privacy-policy-generator/`
- `https://termly.io/products/terms-and-conditions-generator/`
- `https://www.privacypolicies.com/privacy-policy-generator/`
- `https://www.privacypolicies.com/terms-conditions-generator/`

## Plan of Work

1. Add an iPhone/iPad folder-import flow that gives users a real Files-based way to choose a Markdown workspace and that preserves access safely for sandboxed App Store builds.
2. Extend workspace-session persistence so restored folder-backed sessions can survive security-scoped access constraints instead of relying only on raw paths.
3. Add submission-oriented Xcode metadata: privacy manifest, export-compliance setting, app category, opening-documents-in-place behavior, and other low-risk plist/build-setting improvements that do not require icons or App Store Connect.
4. Add repository-owned release-prep documentation, including the concrete website URL map, draft copy goals for support/privacy/terms pages, and the remaining manual App Store Connect steps.
5. Add a release/archive helper so the user has one stable command to run once signing credentials are configured locally.

## Concrete Steps

1. Introduce a cross-platform open-folder action in the scene root and present a folder importer on iPhone/iPad.
2. Add security-scoped bookmark capture/restore for workspace roots and thread it through `WorkspaceWindowSession` and `AppModel`.
3. Update the project file to include a privacy manifest resource and submission-safe Info.plist build settings.
4. Add a release-prep doc and website/legal draft doc under `docs/`, plus a release/archive script under `scripts/`.
5. Add or update focused tests for the new persistence / workspace-selection behavior where practical.
6. Run the narrowest relevant unit/build validations plus `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`.

## Validation and Acceptance

Acceptance for this workstream requires:

- iPhone and iPad code paths expose a real folder-import affordance instead of a fixture-only fallback
- workspace session persistence can store enough information to restore sandboxed folder access where the platform provides security-scoped URLs
- the app bundle includes a privacy manifest resource
- the Xcode project carries basic App Store metadata that can be set locally without icons
- the repository contains concrete website URL recommendations and draft legal/support guidance
- a release/archive helper exists and documents the required signing inputs
- targeted validation passes for the touched code paths, plus `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`

## Idempotence and Recovery

The code/config changes are safe to rerun. If security-scoped restoration misbehaves, recovery is to clear the stored session payload in `UserDefaults` and reopen the workspace through the new picker. If release metadata changes cause an unexpected packaging issue, the generated plist keys can be trimmed without affecting core rendering behavior.

## Artifacts and Notes

Planned validation commands:

- `./scripts/test-unit`
- `./scripts/build --platform macos`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

Useful external references collected before implementation:

- Apple standard EULA: `https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`
- Termly privacy policy generator: `https://termly.io/products/privacy-policy-generator/`
- Termly terms and conditions generator: `https://termly.io/products/terms-and-conditions-generator/`
- PrivacyPolicies.com privacy policy generator: `https://www.privacypolicies.com/privacy-policy-generator/`
- PrivacyPolicies.com terms generator: `https://www.privacypolicies.com/terms-conditions-generator/`

## Interfaces and Dependencies

No new third-party runtime dependencies are expected. The implementation should rely on:

- SwiftUI scene APIs
- `fileImporter` / Uniform Type Identifiers on iPhone and iPad
- platform security-scoped URL / bookmark support where available
- existing repository shell wrappers and docs validation scripts
