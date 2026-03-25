# Code Sample

Markdown Viewer keeps code blocks legible alongside regular prose.

```swift
struct ReleaseChecklist {
    let version: String
    let build: Int

    func summary() -> String {
        "Version \(version) (\(build)) is ready for review."
    }
}

let checklist = ReleaseChecklist(version: "1.0", build: 1)
print(checklist.summary())
```

The app is meant for reading docs, not editing them.
