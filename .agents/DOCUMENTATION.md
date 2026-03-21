# Running implementation notes

- active ExecPlans:
  - `docs/exec-plans/active/2026-03-19-swift-codex-cli-harness.md`
- current milestone:
  - CommonMark semantic corpus parity for the native renderer
- commands run:
  - `xcrun swiftc "Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/Models.swift" "Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/MarkdownRenderer.swift" /tmp/commonmark_repo_probe.swift -o /tmp/commonmark_repo_probe && /tmp/commonmark_repo_probe`
  - `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-commonmark -resultBundlePath /tmp/swift-markdown-viewer-commonmark-3.xcresult -destination platform=macOS,arch=arm64 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testMarkdownRendererMatchesCommonMarkFixtureCorpusSemantics" test`
  - `xcodebuild -quiet -project "Swift Markdown Viewer/Swift Markdown Viewer.xcodeproj" -scheme "Swift Markdown Viewer" -configuration Debug -derivedDataPath /tmp/swift-markdown-viewer-commonmark-noresult -destination platform=macOS,arch=arm64 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY= "-only-testing:Swift Markdown ViewerTests/Swift_Markdown_ViewerTests/testMarkdownRendererMatchesCommonMarkFixtureCorpusSemantics" test`
- evidence gathered:
  - `/tmp/commonmark_repo_probe.swift` now reports `failureCount=0` against `tmp/spec-fixtures/commonmark`
  - `Swift Markdown Viewer/Swift Markdown Viewer/App/Shared/MarkdownRenderer.swift` now preserves paragraph continuation text, strips linked-image placeholders before attributed parsing, and routes declaration/comment text through deterministic HTML-to-text handling
- important discoveries:
  - the largest remaining CommonMark gap was the comparison oracle, not the block tree; AppKit/XML-based HTML extraction was surfacing markup internals as visible text
  - linked-image fixtures require an empty-paragraph result when preprocessing removes all visible markdown, otherwise the parser falls back to legacy raw-text handling
- open risks or blockers:
  - full `xcodebuild` confirmation is currently blocked by host disk exhaustion while Xcode writes log stores and result bundles
  - Safari visual parity remains poor even though CommonMark semantic parity is now at zero mismatches under the repository contract
