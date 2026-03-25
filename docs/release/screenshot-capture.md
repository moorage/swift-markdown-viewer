# Screenshot Capture

Use `scripts/capture-app-store-screenshots` to generate a repeatable set of candidate App Store screenshots and matching harness state/perf snapshots.

## Fixture set

The capture flow uses `Fixtures/app-store/` so the sidebar and document titles read like customer-facing content:

- `Open Markdown Folders.md`
- `Architecture Overview.md`
- `Code Sample.md`
- `Image Preview.md`
- `Navigation Notes.md`

## Command

Run all platforms:

- `./scripts/capture-app-store-screenshots`

Run one platform only:

- `./scripts/capture-app-store-screenshots --platform iphone`
- `./scripts/capture-app-store-screenshots --platform ipad`
- `./scripts/capture-app-store-screenshots --platform macos`

## Output

Artifacts are written under `artifacts/app-store-screenshots/`:

- `iphone/*.png`
- `ipad/*.png`
- `macos/*.png`
- matching `*.state.json`
- matching `*.perf.json`

## Notes

- iPhone and iPad screenshots are captured with `simctl io screenshot` after the app reports a ready state, so they reflect the actual simulator display rather than the harness image exporter.
- The simulator status bar is normalized to `9:41`, full battery, and strong connectivity during iPhone/iPad capture.
- macOS currently relies on the in-app screenshot writer because there is no repo-owned window capture helper yet. The state/perf snapshots are reliable; inspect the generated PNGs before using them in App Store Connect.
