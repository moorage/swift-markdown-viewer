# Free Markdown Viewer Comprehensive Rename and Submission Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Rename the product from `Swift Markdown Viewer` to `Free Markdown Viewer` everywhere that materially defines the app: repository-controlled code, project structure, build and release scripts, docs, website URL guidance, App Store Connect metadata, and Apple identifier surfaces used for submission. The end state should not leave the old product name behind in current operational paths, current release guidance, or current Apple submission records.

This is not a cosmetic string replace. The repo currently has three concurrent identities:

- repository and Xcode identity: `Swift Markdown Viewer`
- app bundle display name and most listing copy: `Markdown Viewer`
- live App Store Connect app record name: `Swift Markdown Viewer`

The rename work therefore needs to collapse all three into one canonical identity: `Free Markdown Viewer`.

The Apple-side work also cannot be treated as a pure in-place rename. The current live app record already has uploaded builds under bundle ID `com.souschefstudio.Swift-Markdown-Viewer`, and Apple treats several of those identifiers as durable. To satisfy the user's request to rename the app "everywhere," this plan assumes a full identity migration to a new bundle ID and new App Store Connect app record, while preserving the old record as a non-shipping legacy artifact unless Apple later allows it to be removed.

## Progress

- [x] (2026-03-27T16:31Z) Read the repository control-plane docs, active release plans, and repo-specific ExecPlan rules before drafting the rename plan.
- [x] (2026-03-27T16:31Z) Audited the checked-in rename blast radius across the Xcode project, scripts, release docs, support URLs, generated docs, and active plans.
- [x] (2026-03-27T16:31Z) Queried the live App Store Connect and bundle-ID state with the repo-owned helper so this plan is grounded in the current Apple-side identifiers and submission status rather than stale assumptions.
- [x] (2026-03-27T16:34Z) Added the active ExecPlan plus the control-plane index update in `.agents/DOCUMENTATION`, then revalidated the repo with `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py`.
- [x] (2026-03-27T17:12Z) Renamed the Xcode project tree, app/test targets, Swift entry points, release docs, and repo-owned script defaults to `Free Markdown Viewer`, then introduced `scripts/lib/product-identity.sh` plus `scripts/verify-product-identity` to centralize and validate the new identity.
- [x] (2026-03-27T17:12Z) Validated the renamed macOS-backed project path with `./scripts/test-unit`, an escalated `./scripts/test-integration`, `python3 scripts/knowledge/generate_repo_map.py`, `python3 scripts/check_execplan.py`, and `python3 scripts/knowledge/check_docs.py`.
- [x] (2026-03-27T17:12Z) Fixed the App Store Connect helper's bundle-id creation flow and created the new bundle ID `com.souschefstudio.Free-Markdown-Viewer` as resource `9ZAXC5Y677`.
- [x] (2026-03-27T17:22Z) Confirmed the new App Store Connect app record `6761271951`, captured its generated app-info and version-localization IDs, and patched the app name/subtitle/privacy URL plus both iOS and macOS listing localizations from the repo-owned release docs.
- [x] (2026-03-27T18:05Z) Archived, exported, uploaded, and attached new iOS/macOS builds for `Free Markdown Viewer`, then repopulated iPhone, iPad, and macOS screenshot sets plus App Review detail records on the new app record.
- [x] (2026-03-27T18:14Z) Rechecked Pricing and Availability after App Store Connect initialized the new record, then confirmed app `6761271951` already matches the legacy Europe-excluded storefront policy exactly without any further territory writes.

## Surprises & Discoveries

- Observation: the repository already carries name drift that is larger than the trademark problem alone.
  Evidence: `README.md` and `ARCHITECTURE.md` still present `Swift Markdown Viewer`, `Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj/project.pbxproj` sets `INFOPLIST_KEY_CFBundleDisplayName = "Markdown Viewer"`, and the live App Store Connect app-info localization currently reports `name = "Swift Markdown Viewer"`.

- Observation: the live App Store Connect record is real and already submission-active.
  Evidence: `./scripts/app-store-connect inspect-app` returns app `6761209087` with name `Swift Markdown Viewer`, bundle ID `com.souschefstudio.Swift-Markdown-Viewer`, and SKU `SWIFTMD`. Additional API reads show app-info state `WAITING_FOR_REVIEW`, iOS version state `REJECTED`, and macOS version state `WAITING_FOR_REVIEW`.

- Observation: the current Apple-side identifiers make a true "rename everywhere" impossible as a pure mutation of the existing record.
  Evidence: Apple documents that apps in `Ready for Review`, `Waiting for Review`, `In Review`, `Metadata Rejected`, or `Rejected` cannot be removed, and that if a build has been uploaded the bundle ID cannot be reused and the SKU cannot be reused in the same organization. The current record is already in `WAITING_FOR_REVIEW` / `REJECTED` states and has two uploaded builds.

- Observation: the existing Bundle ID is registered, while the proposed new one is currently free.
  Evidence: `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Swift-Markdown-Viewer'` returns bundle ID resource `GCX8SVH7K3`, while the same query for `com.souschefstudio.Free-Markdown-Viewer` returns an empty result set.

- Observation: current Apple submission assets are attached to the old record and will not follow a new app record automatically.
  Evidence: the live record has iOS screenshot sets for `APP_IPHONE_67`, `APP_IPAD_PRO_129`, and `APP_IPAD_PRO_3GEN_129`, plus a macOS `APP_DESKTOP` screenshot set, and it already has uploaded iOS and macOS builds. Those relationships are scoped to app/version IDs on the old record.

- Observation: the checked-in repo contains both tracked rename targets and tracked generated files that will need regeneration rather than hand-editing.
  Evidence: tracked paths still include `Swift Markdown Viewer/...`, `docs/release/swift-markdown-viewer-support.md`, `docs/generated/repo-map.json`, and many `Fixtures/expected/spec-safari/**/reference-safari-metadata.json` files that embed the repo slug in absolute paths.

- Observation: the repo rename validation gate should target product identity, not the current repository slug.
  Evidence: after the first implementation pass, `scripts/verify-product-identity` flagged `swift-markdown-viewer` hits in `scripts/lib/product-identity.sh` and the current GitHub issues URL even though the working repository itself still lives at `moorage/swift-markdown-viewer`.

- Observation: sandboxed `xcodebuild test` is not sufficient for every macOS-backed validation path in this environment.
  Evidence: `./scripts/test-integration` failed under the default sandbox with `testmanagerd.control ... Sandbox restriction` and then passed immediately when rerun outside the sandbox.

- Observation: the new App Store Connect app record creates the app-info and version-localization resources immediately, but review-detail resources are still absent until later submission setup steps.
  Evidence: app `6761271951` now exposes app-info `e4dae202-7435-4c97-a82d-c741d5e51384`, app-info localization `a83ddb48-e426-468e-bdca-02050428dc15`, iOS version `ad142231-153d-4b40-b149-bb55cd70b73e`, iOS localization `46cadd66-1413-4ff7-a61d-dc892bee4197`, macOS version `90e1bb1e-5a62-4623-a866-08b2b16262e2`, and macOS localization `561918f2-9ec7-41d1-baa1-c619aa1b3591`, while both `appStoreReviewDetail` relationships still return `data: null`.

- Observation: build upload, screenshot upload, and review-detail creation are fully scriptable on the new record, but storefront availability still cannot be synced until App Store Connect materializes the availability resource.
  Evidence: the new record now has attached valid builds `a4578450-2f16-41ba-ba91-5875d914359c` and `503a3d42-abbc-4043-b017-8ec6d2ffe540`, complete `APP_IPHONE_67`, `APP_IPAD_PRO_3GEN_129`, and `APP_DESKTOP` screenshot sets, and direct `POST /v1/appStoreReviewDetails` calls created iOS review detail `12b5d659-58b7-4adf-b736-66477a19bea9` and macOS review detail `d9779019-7bf4-4632-a046-f114d364782a`, while `GET /v1/apps/6761271951/relationships/appAvailabilityV2` still returns `NOT_FOUND`.

- Observation: once the new app's availability resource materialized, its storefront policy already matched the old record and needed no corrective API writes.
  Evidence: `GET /v1/apps/6761271951/relationships/appAvailabilityV2` now resolves app availability `6761271951`, and a direct comparison of `GET /v2/appAvailabilities/{id}/territoryAvailabilities --query limit=200` across app `6761209087` and app `6761271951` shows the same 42 disabled territories with no missing or extra storefront exclusions.

## Decision Log

- Decision: the canonical product name after this work is `Free Markdown Viewer`.
  Rationale: the user explicitly wants the Apple-owned `Swift` mark removed from the app name, and retaining the current `Swift Markdown Viewer` / `Markdown Viewer` split would keep the repo in a multi-name state.

- Decision: this workstream targets a full identity migration, not only a customer-facing rename.
  Rationale: the request says to rename the app everywhere in the codebase and in Apple's submission surfaces. That includes bundle IDs, SKU choices, project paths, release artifact names, support URLs, and App Store Connect metadata.

- Decision: create a new bundle ID and a new App Store Connect app record rather than trying to repurpose app `6761209087` as the final long-term record.
  Rationale: the current record already has uploaded builds and review states bound to the old identifier family, the old SKU `FREEMD` cannot be reused, and Apple does not let this app be removed in its current state.

- Decision: scrub the old product name from tracked operational files, docs, and generated artifacts, while treating runtime-only `artifacts/` outputs as disposable and not worth manual editing.
  Rationale: the user asked for the rename everywhere in the codebase; tracked repo state should converge to zero operational references to the old product name. Runtime outputs can be regenerated or discarded.

- Decision: centralize product identity values in script-owned configuration as part of the rename.
  Rationale: today the project path, scheme, bundle ID, archive names, support URL slug, and app name are duplicated across scripts and docs. A central identity source reduces the chance of another split-brain naming state.

- Decision: treat App Store Connect app-record creation as a dashboard-only step, but script everything after that point that Apple currently allows through the API.
  Rationale: the repo already proved that metadata, pricing/availability, screenshot assets, build attachment, and inspection are scriptable, while app-record creation itself still requires the App Store Connect UI in the current workflow.

## Outcomes & Retrospective

Pending. When implementation completes, this section should record:

- whether the repo reached zero tracked operational references to `Swift Markdown Viewer`, `Swift-Markdown-Viewer`, `swift-markdown-viewer`, and `SWIFTMD`
- the final chosen bundle ID, SKU, website slug, and GitHub repo slug
- whether the old App Store Connect record was left inert, removed from review, or otherwise retired
- the exact Apple-side commands and UI steps that were required beyond the repo

## Context and Orientation

### Canonical before/after identity map

| Surface | Current | Target |
| --- | --- | --- |
| Product name | `Swift Markdown Viewer` / `Markdown Viewer` | `Free Markdown Viewer` |
| Repo slug | `swift-markdown-viewer` | `free-markdown-viewer` |
| Xcode project dir | `Swift Markdown Viewer/` | `Free Markdown Viewer/` |
| Xcode scheme | `Free Markdown Viewer` | `Free Markdown Viewer` |
| App bundle ID | `com.souschefstudio.Swift-Markdown-Viewer` | `com.souschefstudio.Free-Markdown-Viewer` |
| Current SKU | `SWIFTMD` | `FREEMD` |
| Marketing URL slug | `/apps/swift-markdown-viewer` | `/apps/free-markdown-viewer` |
| Support doc filename | `docs/release/swift-markdown-viewer-support.md` | `docs/release/free-markdown-viewer-support.md` |

### Local repo surfaces that currently encode the old identity

- `README.md`
- `README_FOR_APES.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `.agents/DOCUMENTATION.md`
- `Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj/project.pbxproj`
- `Swift Markdown Viewer/Swift Markdown Viewer/Swift_Markdown_ViewerApp.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerTests/Swift_Markdown_ViewerTests.swift`
- `Swift Markdown Viewer/Swift Markdown ViewerUITests/Swift_Markdown_ViewerUITests.swift`
- `scripts/lib/xcode-env.sh`
- `scripts/archive-release`
- `scripts/export-app-store`
- `scripts/capture-app-store-screenshots`
- `scripts/knowledge/generate_repo_map.py`
- `scripts/knowledge/suggest_doc_updates.py`
- `scripts/knowledge/update_quality_score.py`
- `docs/release/app-store-submission.md`
- `docs/release/release-completion-checklist.md`
- `docs/release/app-store-metadata.md`
- `docs/release/free-markdown-viewer-support.md`
- `docs/generated/repo-map.json`

### Apple-side identifiers and live records captured during planning

- old app record ID: `6761209087`
- old app name: `Swift Markdown Viewer`
- old app bundle ID: `com.souschefstudio.Swift-Markdown-Viewer`
- old app SKU: `SWIFTMD`
- old bundle-ID resource ID: `GCX8SVH7K3`
- old app-info resource ID: `891065b1-0cd2-4c27-85c6-b2e370e6ba5a`
- old app-info localization ID: `70d555ee-7fb1-45b5-8a45-24e47f6dcdba`
- old iOS version ID: `9fe8035c-4b97-462a-b51a-5b796b4a74f8`
- old iOS version-localization ID: `db7c072b-a41a-46aa-be1d-f0b78a8285c0`
- old iOS review-detail ID: `b1d7f4b3-5d35-490a-9446-9c28b3bd896a`
- old macOS version ID: `3e7ec5c9-2fc8-4c19-8604-cbaa13060783`
- old macOS version-localization ID: `53c9a854-c8b8-47a0-a09d-7ae0f01aa053`
- old macOS review-detail ID: `994b7637-25fc-4044-b680-e86cfc392a00`

### Apple-side constraints that shape the plan

- App Store Connect metadata and pricing are scriptable through the App Store Connect REST API after the app record exists.
- App Store Connect app-record creation still needs the dashboard in the current repo workflow.
- Apple says apps in `Ready for Review`, `Waiting for Review`, `In Review`, `Metadata Rejected`, or `Rejected` cannot be removed.
- Apple says that if an uploaded build exists, the removed app's bundle ID cannot be reused and the SKU cannot be reused in the same organization.
- The current record already has uploaded builds and is in `WAITING_FOR_REVIEW` / `REJECTED` states, so the old record must be treated as legacy rather than the final renamed submission vehicle.

## Plan of Work

1. Freeze a single canonical identity spec for `Free Markdown Viewer`, including product name, repo slug, scheme, bundle ID family, SKU strategy, and website paths.
2. Add repo-owned identity helpers and verification checks so the rename is centralized and future drift is detectable.
3. Rename all local tracked code, tests, project structure, script defaults, and current docs from the old names to the new ones.
4. Regenerate tracked generated artifacts that embed old names or paths instead of hand-editing them.
5. Prepare Apple-side migration automation for bundle-ID inspection/creation, metadata syncing, screenshot syncing, availability syncing, and build attachment.
6. Create a new App Store Connect app record in the UI, then finish the rename on Apple surfaces through repo-owned scripts wherever Apple permits.
7. Rebuild and re-upload iOS and macOS binaries under the new bundle ID, attach them to the new app record, and reconstitute screenshots and submission metadata there.
8. Verify that the repo and the new Apple record are both consistently branded as `Free Markdown Viewer`, and document the disposition of the legacy `Swift Markdown Viewer` record.

## Concrete Steps

### Phase 0: Freeze the identity spec and capture rollback artifacts

1. Create a checked-in identity matrix that names the exact target strings:
   - product name: `Free Markdown Viewer`
   - repo slug: `free-markdown-viewer`
   - app bundle ID: `com.souschefstudio.Free-Markdown-Viewer`
   - test bundle IDs: new `Free-Markdown-Viewer` suffixes
   - website paths: `/apps/free-markdown-viewer` and `/apps/free-markdown-viewer/support`
   - new non-reused SKU, replacing `SWIFTMD`

2. Save current Apple-side state into `artifacts/rename-audit/` using the existing helper so the migration always has a read-only rollback snapshot:
   - `./scripts/app-store-connect inspect-app --raw > artifacts/rename-audit/old-app.json`
   - `./scripts/app-store-connect request GET /v1/apps/6761209087/appInfos --query include=appInfoLocalizations > artifacts/rename-audit/old-appInfos.json`
   - `./scripts/app-store-connect request GET /v1/apps/6761209087/appStoreVersions --query include=appStoreVersionLocalizations,appStoreReviewDetail > artifacts/rename-audit/old-appStoreVersions.json`
   - `./scripts/app-store-connect request GET /v1/apps/6761209087/builds > artifacts/rename-audit/old-builds.json`
   - `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Swift-Markdown-Viewer' > artifacts/rename-audit/old-bundle-id.json`

3. Add a preflight scan command that becomes the rename gate:
   - `rg -n --hidden -S 'Swift Markdown Viewer|Swift-Markdown-Viewer|swift-markdown-viewer|SWIFTMD' .`
   The implementation should drive this toward zero tracked operational hits before completion.

### Phase 1: Centralize identity configuration before bulk edits

4. Introduce a shared identity config for scripts and release docs, for example `scripts/lib/product-identity.sh` plus a small machine-readable companion if useful.

5. Route the existing release and harness scripts through that identity config:
   - `scripts/lib/xcode-env.sh`
   - `scripts/archive-release`
   - `scripts/export-app-store`
   - `scripts/capture-app-store-screenshots`
   - `scripts/test-unit`
   - `scripts/test-integration`
   - `scripts/build`
   - any script that computes project paths, scheme names, app paths, archive names, or bundle IDs

6. Add a repo-owned rename verification helper such as `scripts/verify-product-identity` that fails when old tracked identity strings remain in current operational surfaces.

### Phase 2: Rename the local codebase and project structure

7. Rename the checked-in directory and file surfaces with `git mv` rather than ad hoc copy/delete:
   - `Swift Markdown Viewer/` -> `Free Markdown Viewer/`
   - `Swift Markdown Viewer/Swift Markdown Viewer/` -> `Free Markdown Viewer/Free Markdown Viewer/`
   - `Swift Markdown Viewer/Swift Markdown ViewerTests/` -> `Free Markdown Viewer/Free Markdown ViewerTests/`
   - `Swift Markdown Viewer/Swift Markdown ViewerUITests/` -> `Free Markdown Viewer/Free Markdown ViewerUITests/`
   - `Swift_Markdown_ViewerApp.swift` -> `Free_Markdown_ViewerApp.swift`
   - `Swift_Markdown_ViewerTests.swift` -> `Free_Markdown_ViewerTests.swift`
   - `Swift_Markdown_ViewerUITests.swift` -> `Free_Markdown_ViewerUITests.swift`
   - `Swift_Markdown_ViewerUITestsLaunchTests.swift` -> `Free_Markdown_ViewerUITestsLaunchTests.swift`
   - `docs/release/swift-markdown-viewer-support.md` -> `docs/release/free-markdown-viewer-support.md`

8. Update `Free Markdown Viewer/Free Markdown Viewer.xcodeproj/project.pbxproj` comprehensively:
   - project name
   - app target name
   - unit-test and UI-test target names
   - product references
   - build configuration list display names
   - group paths
   - scheme references if shared schemes are added or regenerated
   - `PRODUCT_BUNDLE_IDENTIFIER` for app and tests
   - `TEST_TARGET_NAME`
   - `TEST_HOST`
   - `INFOPLIST_KEY_CFBundleDisplayName`
   - any other `Swift Markdown Viewer` / `Swift-Markdown-Viewer` strings

9. Update Swift source and tests so symbols, titles, and test bundles align with the renamed target/module family:
   - `@main` app type name
   - test class names and launch-test scaffolding
   - UI-test bundle references
   - any string literals that surface the product name or target name

10. Update asset, harness, and release path assumptions that include the product name:
   - app bundle paths under DerivedData
   - archive names
   - export names
   - package upload filenames
   - screenshot output paths
   - checkpoint names or bundle lookups that currently depend on `Free Markdown Viewer.app`

### Phase 3: Rename docs, website guidance, and current control-plane references

11. Rewrite the current human-facing and agent-facing docs to use the new identity:
   - `README.md`
   - `README_FOR_APES.md`
   - `AGENTS.md`
   - `ARCHITECTURE.md`
   - `docs/harness.md`
   - `docs/debug-contracts.md`

12. Rewrite release and submission docs so every public-facing recommendation uses `Free Markdown Viewer`:
   - `docs/release/app-store-submission.md`
   - `docs/release/release-completion-checklist.md`
   - `docs/release/app-store-metadata.md`
   - `docs/release/app-review-notes.md`
   - `docs/release/privacy-policy-draft.md`
   - `docs/release/terms-of-use-draft.md`
   - `docs/release/index.md`
   - `docs/release/free-markdown-viewer-support.md`

13. Update active ExecPlans and `.agents/DOCUMENTATION` so the current control plane stops teaching or repeating the old name in commands, paths, and evidence blocks.

14. Decide whether to rewrite historical docs outside the active control plane. If the goal is truly zero old-name strings in tracked files, include a final historical scrub pass after the core rename. If preserving exact historical prose matters more, document the explicit allowlist and exclude only those files from the zero-hit gate.

15. Update all website and support references that currently use the old slug:
   - `https://www.matthewpaulmoore.com/apps/free-markdown-viewer`
   - `https://www.matthewpaulmoore.com/apps/free-markdown-viewer/support`
   - `https://github.com/moorage/free-markdown-viewer/issues`

### Phase 4: Regenerate tracked generated artifacts instead of hand-editing them

16. Refresh tracked generated docs after the rename:
   - `python3 scripts/knowledge/generate_repo_map.py`
   - `python3 scripts/knowledge/update_quality_score.py`

17. If the local repo folder is renamed on disk from `swift-markdown-viewer` to `free-markdown-viewer`, regenerate any checked-in expected files that encode absolute workspace paths, especially:
   - `Fixtures/expected/spec-safari/**/reference-safari-metadata.json`
   - any repo-generated metadata snapshots that record the repo root path

18. Treat runtime-only directories under `artifacts/` as disposable. Do not hand-edit them. Delete or regenerate them after the identity change instead.

### Phase 5: Extend Apple automation for the rename migration

19. Expand `scripts/lib/app_store_connect.py` and `scripts/app-store-connect` beyond `request` and `inspect-app` so the repo owns first-class rename/migration commands. At minimum add subcommands for:
   - inspecting old and new bundle-ID/app-record state
   - creating or verifying a new bundle ID
   - patching app-info localizations
   - patching app-store-version localizations
   - patching app-review details and notes
   - syncing availability from one app to another
   - listing screenshot sets and clearing/re-uploading them
   - attaching builds to app-store versions
   - asserting that current live metadata matches the canonical identity file

20. Keep all Apple write paths read-before-write and idempotent:
   - inspect current state first
   - no blind POST or PATCH calls
   - tolerate reruns if the new app record is partially configured
   - store emitted IDs under `artifacts/rename-audit/` so later steps do not require rediscovery by hand

### Phase 6: Create new Apple identifiers and the new app record

21. Create the new bundle ID `com.souschefstudio.Free-Markdown-Viewer`.
   Preferred path:
   - use a repo-owned App Store Connect / Certificates, IDs & Profiles API command once added
   Fallback:
   - create it in the Apple Developer dashboard if Apple blocks that API path for the configured key

22. Verify that the new bundle ID exists and that the old one remains intact:
   - `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Free-Markdown-Viewer'`
   - `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Swift-Markdown-Viewer'`

23. Create a brand-new App Store Connect app record manually in the dashboard because this remains UI-only in the current workflow.
   Planned values:
   - App name: `Free Markdown Viewer`
   - Platforms: `iOS` and `macOS`
   - Primary language: `English (U.S.)`
   - Bundle ID: `com.souschefstudio.Free-Markdown-Viewer`
   - SKU: new non-reused value, replacing `SWIFTMD`
   - User access: `Full Access` unless the user wants tighter app-level permissions

24. Immediately capture the new app record and its generated resource IDs with the helper and save them under `artifacts/rename-audit/new-*.json`.

### Phase 7: Script the post-create App Store Connect rename state

25. Patch app-info localization data on the new record so the install-facing name and subtitle are correct:
   - name: `Free Markdown Viewer`
   - subtitle: updated final copy with no `Swift` / old-name residue
   - privacy policy URL: new live URL if the website slug changes

26. Patch iOS and macOS version-localization data on the new record:
   - description
   - keywords
   - promotional text
   - marketing URL
   - support URL
   - "what's new" if the new record is not a 1.0 clean start

27. Patch review details and notes so App Review sees the new product name and any migration explanation it needs:
   - reviewer contact
   - review notes
   - attachment references if used later

28. Reapply pricing and availability on the new record to match the current intended release posture, including any Europe exclusions already configured on the old record.

29. Re-upload screenshots to the new record because screenshot sets do not transfer across app records.
   Use repo-owned assets and the capture flow:
   - `./scripts/capture-app-store-screenshots`
   - new upload subcommands built on top of the App Store Connect API

30. Recreate any app-review attachments on the new record if they are added later. The current old record has zero review attachments, so this is only a future-proofing step.

### Phase 8: Rebuild and upload new binaries under the new identity

31. Archive iOS and macOS builds with the new bundle ID and new product name:
   - `APPLE_DEVELOPMENT_TEAM=<TEAM_ID> APP_BUNDLE_IDENTIFIER_OVERRIDE=com.souschefstudio.Free-Markdown-Viewer ./scripts/archive-release --platform ios --allow-provisioning-updates`
   - `APPLE_DEVELOPMENT_TEAM=<TEAM_ID> APP_BUNDLE_IDENTIFIER_OVERRIDE=com.souschefstudio.Free-Markdown-Viewer ./scripts/archive-release --platform macos --allow-provisioning-updates`

32. Export App Store packages from those archives:
   - `./scripts/export-app-store --platform ios --archive-path <new-ios-xcarchive> --export-options-plist <plist> --allow-provisioning-updates`
   - `./scripts/export-app-store --platform macos --archive-path <new-macos-xcarchive> --export-options-plist <plist> --allow-provisioning-updates`

33. Upload the new packages to App Store Connect and inspect the resulting build records to confirm the new app record, new bundle ID, and new product name are all aligned.

34. Attach the new builds to the new iOS and macOS app-store versions through the repo-owned helper once the build processing state is `VALID`.

35. If needed, remove or leave unattached the old record's versions and builds. Do not depend on the old builds for the renamed submission.

### Phase 9: Handle the legacy `Swift Markdown Viewer` record safely

36. Do not try to reuse the old SKU `SWIFTMD`, old bundle ID, or old uploaded builds.

37. Decide how the old record should be left after the new record is healthy:
   - remove it from review if that state transition becomes available
   - clear availability if appropriate
   - leave it as a non-shipping placeholder if Apple will not permit full removal

38. Document the exact old-record disposition in the release docs so future maintainers know why two records exist and which one is canonical.

## Validation and Acceptance

Acceptance requires all of the following:

- a tracked-file scan for `Swift Markdown Viewer`, `Swift-Markdown-Viewer`, `swift-markdown-viewer`, and `SWIFTMD` returns zero operational hits, or only a deliberate documented allowlist
- the renamed Xcode project builds and test commands work using `Free Markdown Viewer` paths, scheme names, and bundle names
- `scripts/lib/xcode-env.sh` and all repo-owned release helpers default to the new identity values
- release docs, support docs, privacy/legal drafts, and website URL guidance all point at `Free Markdown Viewer` and the new slug
- tracked generated files such as `docs/generated/repo-map.json` and any path-sensitive fixture metadata have been regenerated after the rename
- a new bundle ID for `com.souschefstudio.Free-Markdown-Viewer` exists and is queryable through the helper
- a new App Store Connect app record exists for `Free Markdown Viewer` and the helper can inspect it by the new bundle ID
- the new record's app-info localization, version localizations, support/marketing/privacy URLs, pricing/availability, screenshots, and review notes are all updated to the new identity
- new iOS and macOS builds are archived, exported, uploaded, and attached under the new bundle ID and new app record
- `python3 scripts/check_execplan.py` and `python3 scripts/knowledge/check_docs.py` pass after the plan and doc updates

Recommended repo validation loop after implementation:

- `./scripts/build --platform all`
- `./scripts/test-unit`
- `./scripts/test-integration`
- `./scripts/test-ui-macos --smoke`
- `./scripts/test-ui-ios --device both --smoke`
- `./scripts/capture-app-store-screenshots`
- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`
- `rg -n --hidden -S 'Swift Markdown Viewer|Swift-Markdown-Viewer|swift-markdown-viewer|SWIFTMD' .`

Recommended Apple-side validation loop after migration:

- `./scripts/app-store-connect inspect-app --bundle-id com.souschefstudio.Free-Markdown-Viewer`
- `./scripts/app-store-connect request GET /v1/bundleIds --query 'filter[identifier]=com.souschefstudio.Free-Markdown-Viewer'`
- repo-owned metadata assertion commands for the new app-info localization, version localizations, availability, screenshots, and build attachments

## Idempotence and Recovery

The local repo rename should happen on a dedicated git branch and remain safe to rerun. File moves should use `git mv`, scriptable content edits should be deterministic, and generated files should be regenerated from source commands rather than manually maintained.

The Apple-side workflow must be read-before-write and safe to resume:

- the old app record remains the emergency fallback and should not be destructively modified until the new record is fully configured
- new helper commands should inspect for existing bundle IDs, app records, localizations, screenshot sets, and attached builds before creating or patching anything
- artifact snapshots in `artifacts/rename-audit/` should capture all important old and new resource IDs so a partial run can continue later
- if the new bundle ID is created but the new app record is not yet created, that intermediate state is acceptable
- if the new app record exists but metadata is incomplete, rerunning the sync commands should converge it without duplicate resources
- if the new record fails submission validation, the old record and old uploaded builds should remain untouched as a rollback safety net

Recovery for the local repo name and slug is separate from git history:

- renaming the top-level clone directory from `swift-markdown-viewer` to `free-markdown-viewer` is an external filesystem operation, not a tracked git rename
- if that local root rename is performed, regenerate any path-bearing checked-in metadata immediately afterward

## Artifacts and Notes

Planned repo artifacts for this workstream:

- `artifacts/rename-audit/old-app.json`
- `artifacts/rename-audit/old-appInfos.json`
- `artifacts/rename-audit/old-appStoreVersions.json`
- `artifacts/rename-audit/old-builds.json`
- `artifacts/rename-audit/old-bundle-id.json`
- matching `new-*.json` artifacts after the new record exists

Planned validation commands for the planning change itself:

- `python3 scripts/check_execplan.py`
- `python3 scripts/knowledge/check_docs.py`

Useful Apple references captured during planning:

- Add a new app: `https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app`
- View and edit app information: `https://developer.apple.com/help/app-store-connect/create-an-app-record/view-and-edit-app-information`
- Remove an app: `https://developer.apple.com/help/app-store-connect/create-an-app-record/remove-an-app`
- Upload app previews and screenshots: `https://developer.apple.com/help/app-store-connect/manage-app-information/upload-app-previews-and-screenshots`
- Submit an app: `https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-app`
- Required, localizable, and editable properties: `https://developer.apple.com/help/app-store-connect/reference/app-information/required-localizable-and-editable-properties`

Apple-side facts taken from those references and from live inspection:

- app metadata, pricing, and screenshot assets are API-manageable after the app record exists
- the new app record itself is still treated as a dashboard step in this repo workflow
- the current old record cannot be removed in its current states
- the old bundle ID and old SKU are not reusable for the final renamed app path
- the new bundle ID `com.souschefstudio.Free-Markdown-Viewer` now exists in Apple as bundle-ID resource `9ZAXC5Y677`
- the new app record `6761271951` now exists for `Free Markdown Viewer`, and its first-pass listing metadata has been patched onto the generated en-US app-info and version-localization records

## Interfaces and Dependencies

This work depends on:

- the existing repo-owned harness and release scripts under `scripts/`
- `xcodebuild`, `xcrun`, and full Xcode for archive/build/test work
- App Store Connect API credentials via `ASC_KEY_ID`, `ASC_ISSUER_ID`, and `ASC_KEY_PATH`
- Apple signing via `APPLE_DEVELOPMENT_TEAM`
- the App Store Connect REST API for post-create metadata, availability, screenshot, and build automation
- Apple dashboards for the new app-record creation step and any UI-only verification steps
- the live website / support destination for the new `/apps/free-markdown-viewer` paths
- optional GitHub repo rename if the support link should stop using `moorage/free-markdown-viewer`
