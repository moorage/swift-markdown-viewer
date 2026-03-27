# App Store Connect Release Setup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Use the locally configured App Store Connect API key to move the app from repository-only release readiness into actual App Store Connect setup. The target outcome is a repeatable repo-owned command surface that can inspect the existing app record, create it if missing, and configure territory availability for the live release posture the user wants: ship on macOS and iOS/iPadOS, and keep Europe excluded for now because of extra legal requirements. The repo should also document what was automated, what remains manual, and what exact territory scope was used.

## Progress

- [x] (2026-03-26T18:54Z) Created this ExecPlan and started auditing the existing repository release scripts, docs, and App Store Connect prerequisites.
- [x] (2026-03-26T19:36Z) Added a repo-owned `scripts/app-store-connect` helper that authenticates with the local API key, issues App Store Connect API requests, and can inspect the app-record state for the repo bundle ID.
- [x] (2026-03-26T19:44Z) Confirmed that the real bundle ID is `com.souschefstudio.Swift-Markdown-Viewer`, that its bundle ID record already exists in Apple’s systems, and that no App Store Connect app record exists yet.
- [x] (2026-03-26T19:46Z) Confirmed via a live API attempt that App Store Connect does not allow app-record creation through the REST API for this resource; the app record must be created manually in the UI before post-creation automation can proceed.
- [x] (2026-03-26T19:49Z) Corrected the repo helper bundle-ID default to `com.souschefstudio.Swift-Markdown-Viewer` and documented the new App Store Connect helper plus the required manual app-record creation step in the release docs.
- [x] (2026-03-26T20:18Z) After the user created app record `6761209087`, confirmed that App Store Connect now has both `IOS` and `MAC_OS` app-store versions in `PREPARE_FOR_SUBMISSION`.
- [x] (2026-03-26T20:28Z) Applied repo-owned listing metadata through the API: primary category `PRODUCTIVITY`, subtitle, privacy policy URL, support URL, marketing URL, promotional text, description, and keywords.
- [x] (2026-03-26T20:31Z) Confirmed that the app-availability resource is still not materialized through the API, so storefront restriction setup remains blocked on a Pricing and Availability UI step in App Store Connect.
- [x] (2026-03-26T20:38Z) After Pricing and Availability was initialized in the UI, confirmed that the `appAvailabilityV2` resource now resolves and that the live storefront state already matches the requested policy: Europe disabled, non-Europe enabled.
- [x] (2026-03-26T20:20Z) Added auth-key-aware `xcodebuild` export/archive support, produced signed iOS and macOS archives plus App Store export artifacts, and uploaded both builds to App Store Connect.
- [x] (2026-03-26T20:24Z) Fixed the iOS App Store icon rejection by removing alpha from the 1024 App Store icon variants, then rebuilt and re-uploaded the iOS package successfully.
- [x] (2026-03-26T20:41Z) Attached the valid iOS and macOS builds to their respective draft App Store versions through the API.
- [x] (2026-03-26T20:54Z) Updated screenshot capture automation to target release-grade iPhone, iPad, and macOS dimensions, regenerated the screenshot set, and uploaded accepted iPhone, iPad, and macOS screenshots to App Store Connect.

## Surprises & Discoveries

- Observation: the repository already covers most local release prep, but it does not yet own any App Store Connect API helper or live app-record automation.
  Evidence: `scripts/` contains archive/export/screenshot helpers, while a repo-wide search shows no App Store Connect API client or JWT helper.

- Observation: the repository’s helper shell config had drifted away from the actual app target bundle identifier.
  Evidence: `scripts/lib/xcode-env.sh` was still using `com.matthewpaulmoore.Swift-Markdown-Viewer`, while `Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj/project.pbxproj` sets the app target bundle ID to `com.souschefstudio.Swift-Markdown-Viewer`.

- Observation: the bundle identifier already exists in Apple’s bundle ID registry, but the App Store Connect app record does not.
  Evidence: `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Swift-Markdown-Viewer' --query limit=5` returned bundle ID `GCX8SVH7K3`, while both `./scripts/app-store-connect inspect-app` and `./scripts/app-store-connect request GET /v1/apps --query 'filter[bundleId]=com.souschefstudio.Swift-Markdown-Viewer' --query limit=5` returned zero app records.

- Observation: the App Store Connect REST API rejects app-record creation for the `apps` resource.
  Evidence: `./scripts/app-store-connect request POST /v1/apps ...` returned `FORBIDDEN_ERROR` with `The resource 'apps' does not allow 'CREATE'. Allowed operations are: GET_COLLECTION, GET_INSTANCE, UPDATE`.

- Observation: once the app record existed, both Apple-supported release platforms were created immediately for the app.
  Evidence: `./scripts/app-store-connect request GET /v1/apps/6761209087/appStoreVersions --query limit=20` returned one `IOS` version and one `MAC_OS` version, both at `1.0` and `PREPARE_FOR_SUBMISSION`.

- Observation: App Store Connect allowed metadata writes for localizations and app info, but not through the `primaryCategory` relationship endpoint.
  Evidence: `PATCH /v1/appInfos/.../relationships/primaryCategory` returned `FORBIDDEN_ERROR`, while `PATCH /v1/appInfos/{id}` with a `relationships.primaryCategory` payload succeeded, and both `PATCH /v1/appInfoLocalizations/{id}` plus `PATCH /v1/appStoreVersionLocalizations/{id}` succeeded.

- Observation: the app-availability resource still returns `NOT_FOUND` even after the app record and metadata were created.
  Evidence: `./scripts/app-store-connect request GET /v1/apps/6761209087/relationships/appAvailabilityV2` returned `There is no resource of type 'appAvailabilities' with id '6761209087'`.

- Observation: once Pricing and Availability was saved in the App Store Connect UI, the mixed-surface availability resource became available and showed the desired storefront policy already in place.
  Evidence: `./scripts/app-store-connect request GET /v1/apps/6761209087/relationships/appAvailabilityV2` now returns app availability `6761209087`, and a direct read of `./scripts/app-store-connect request GET /v2/appAvailabilities/6761209087/territoryAvailabilities --query limit=200` shows all sampled European storefronts with `available=false` while a full scan found `COUNT=0` disabled storefronts outside the repository’s Europe set.

- Observation: `xcodebuild` App Store export accepts App Store Connect authentication keys, but only when the key path is an absolute filesystem path.
  Evidence: both `./scripts/export-app-store` invocations failed with `The -authenticationKeyPath flag must be an absolute path to an existing file` until `scripts/lib/xcode-env.sh` started resolving repo-root-relative `.env` paths to absolute paths.

- Observation: Apple transport rejected the first iOS upload because the 1024 App Store icon assets still contained an alpha channel.
  Evidence: `xcrun altool --upload-package "artifacts/exports/ios/Swift Markdown Viewer.ipa" ...` returned `Invalid large app icon ... can’t be transparent or contain an alpha channel`, and `sips -g hasAlpha` reported `yes` for all three `icon-ios-1024*.png` variants before they were flattened.

- Observation: the repo screenshot capture defaults were aimed at preview-friendly device/window sizes, not the exact App Store upload buckets.
  Evidence: the first generated screenshot set measured `1206x2622` on iPhone, `1668x2420` on iPad, and `2880x2048` on macOS; after updating the capture preferences and Mac window size, the regenerated set measured `1320x2868`, `2064x2752`, and `2880x1800`.

- Observation: current App Store Connect screenshot upload accepts `APP_IPHONE_67`, `APP_IPAD_PRO_3GEN_129`, and `APP_DESKTOP` for this app, while the older `APP_IPAD_PRO_129` bucket fails validation against modern 13-inch iPad captures.
  Evidence: uploading `2064x2752` screenshots into screenshot set `65ece46b-4e1e-439e-a05b-fd479e7b0d18` (`APP_IPAD_PRO_129`) failed with `IMAGE_INCORRECT_DIMENSIONS`, while the same files uploaded successfully into screenshot set `1b3e5c0b-3fd5-4560-97c6-cc450a2f992e` (`APP_IPAD_PRO_3GEN_129`).

- Observation: Apple currently returns a server-side error when deleting the now-empty obsolete iPad screenshot set created under the wrong display bucket.
  Evidence: `DELETE /v1/appScreenshotSets/65ece46b-4e1e-439e-a05b-fd479e7b0d18` returned `500 UNEXPECTED_ERROR` even after its only failed screenshot resource had been deleted successfully.

## Decision Log

- Decision: treat the Europe exclusion scope as a first-class documented configuration in the repo instead of hard-coding an undocumented country list.
  Rationale: territory exclusions are high-stakes release settings. The exact scope must be explicit and reviewable before it is applied to a live App Store Connect record.
  Date/Author: 2026-03-26 / Codex

## Outcomes & Retrospective

The repo now has a reusable App Store Connect helper that authenticates with the locally configured API key and can inspect live ASC resources without exposing secret material. That closes the tooling gap between repository-only release prep and live ASC inspection.

The critical blocker turned out not to be authentication but product-record creation. The bundle identifier already exists and is ready to use, but Apple currently requires the actual App Store Connect app record to be created through the App Store Connect UI. Because the record does not exist yet, territory-availability automation and post-creation metadata updates must wait until that one manual step is complete.

After the manual app-record creation step, the repo automation was able to populate the app’s core listing metadata successfully. The app now has both iOS and macOS versions, the `PRODUCTIVITY` category, a subtitle, the privacy-policy/support/marketing URLs, and platform-localized description, keywords, and promotional text drawn from the repo-owned release drafts.

The storefront policy is also now in the desired state. After a one-time Pricing and Availability save in App Store Connect, the app-availability resource resolved and confirmed that European storefronts are disabled while non-European storefronts remain enabled. No further territory write was required in this session.

The signed build path is now working end to end from the repo. `scripts/archive-release` and `scripts/export-app-store` can consume the locally configured App Store Connect key when provisioning updates are enabled, both platforms exported successfully, the iOS icon alpha issue was corrected locally, and App Store Connect now shows valid uploaded build records for both iOS and macOS. Those builds are also attached to the draft app-store versions through the API.

The screenshot path is also live. The repo capture helper now targets App Store-accepted output sizes by default, the regenerated screenshot set covers iPhone, iPad, and macOS at accepted dimensions, and the uploaded screenshot assets are complete in App Store Connect for the real iPhone, iPad, and desktop screenshot buckets. The only residual oddity is an empty obsolete iPad screenshot set under the older `APP_IPAD_PRO_129` bucket that Apple’s API currently refuses to delete with a server-side `500`.

## Context and Orientation

Relevant areas:

- `scripts/lib/xcode-env.sh`
- `scripts/archive-release`
- `scripts/export-app-store`
- `docs/release/app-store-submission.md`
- `docs/release/release-completion-checklist.md`
- App Store Connect API and App Store Connect Help pages for app records, platforms, and availability

## Plan of Work

1. Audit the current App Store Connect state using the locally provided API key and determine whether the app record already exists.
2. Add repo-owned scripts for App Store Connect authentication, inspection, and territory-availability configuration.
3. Apply safe live changes for the app record and availability, excluding Europe under a documented territory set.
4. Update release docs plus implementation notes with the exact commands, scope, and residual manual steps.

## Concrete Steps

1. Build a local JWT/auth helper that reads `ASC_KEY_ID`, `ASC_ISSUER_ID`, and `ASC_KEY_PATH`.
2. Add a script that can query apps, bundle IDs, territories, and availability relationships from App Store Connect.
3. Decide and document the Europe exclusion set before applying it.
4. Create or update the app record and territory availability via App Store Connect where the API and account permissions allow it.
5. Run the narrowest repo verification loop for touched scripts/docs and capture the exact outcomes.

## Validation and Acceptance

Acceptance requires:

- repo-owned App Store Connect scripts authenticate successfully with the local API key
- the scripts can report the current live app-record state for this bundle ID
- the release docs explain how to use the new command surface and what remains manual
- any applied live configuration is documented, including the exact Europe exclusion scope
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass after the plan/docs changes

## Idempotence and Recovery

The scripts should be safe to rerun. Live configuration changes must prefer read-before-write behavior and emit clear output so a later pass can confirm or correct the state. Any territory-availability change must be reversible by rerunning the script with an explicit replacement set.

## Artifacts and Notes

Planned validation commands:

- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

Key live commands used in this session:

- `APPLE_DEVELOPMENT_TEAM=GG34PA8F4A ./scripts/archive-release --platform ios`
- `APPLE_DEVELOPMENT_TEAM=GG34PA8F4A ./scripts/archive-release --platform macos`
- `./scripts/export-app-store --platform ios --archive-path "artifacts/archives/Swift Markdown Viewer-ios.xcarchive" --export-options-plist "artifacts/export-options/ios-app-store-connect.plist" --allow-provisioning-updates`
- `./scripts/export-app-store --platform macos --archive-path "artifacts/archives/Swift Markdown Viewer-macos.xcarchive" --export-options-plist "artifacts/export-options/macos-app-store-connect.plist" --allow-provisioning-updates`
- `xcrun altool --upload-package "artifacts/exports/ios/Swift Markdown Viewer.ipa" ...`
- `xcrun altool --upload-package "artifacts/exports/macos/Swift Markdown Viewer.pkg" ...`
- `./scripts/app-store-connect request PATCH /v1/appStoreVersions/{id}/relationships/build ...`
- `./scripts/capture-app-store-screenshots --platform iphone`
- `./scripts/capture-app-store-screenshots --platform ipad`
- `./scripts/capture-app-store-screenshots --platform macos`

## Interfaces and Dependencies

The implementation should rely on:

- the repo-root `.env` / shell environment for App Store Connect credentials
- standard macOS shell tools plus Python 3 standard library where practical
- official App Store Connect API endpoints and official Apple help/docs for product and availability behavior
