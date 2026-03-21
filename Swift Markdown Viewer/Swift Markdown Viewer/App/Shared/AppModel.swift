import Combine
import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
    @Published private(set) var files: [MarkdownFileNode] = []
    @Published private(set) var documentText = "Loading…"
    @Published private(set) var documentBlocks: [MarkdownBlock] = []
    @Published private(set) var selectedPath: WorkspacePath?
    @Published private(set) var backStack: [NavigationEntry] = []
    @Published private(set) var forwardStack: [NavigationEntry] = []
    @Published private(set) var workspaceRootDisplay = "Fixtures/docs"
    @Published private(set) var isReady = false
    @Published var viewportSize: CGSize = CGSize(width: 1100, height: 900)

    let launchOptions: HarnessLaunchOptions

    private let startReference = Date()
    private var readyReference = Date()
    private var bootstrapTask: Task<Void, Never>?
    private var commandServer: HarnessCommandServer?
    private var didWriteLaunchArtifacts = false
    private var workspaceProvider: WorkspaceProvider?
    private var screenshotWriter: ((URL) throws -> Void)?

    init(launchOptions: HarnessLaunchOptions) {
        self.launchOptions = launchOptions
    }

    var canNavigateBack: Bool {
        !backStack.isEmpty
    }

    var canNavigateForward: Bool {
        !forwardStack.isEmpty
    }

    var selectedFileDisplayName: String {
        selectedPath?.rawValue.split(separator: "/").last.map(String.init) ?? "No file selected"
    }

    var windowTitle: String {
        "\(workspaceRootDisplay) > \(selectedFileDisplayName)"
    }

    static var preview: AppModel {
        let model = AppModel(launchOptions: HarnessLaunchOptions.fromProcess(arguments: ["Preview"]))
        model.files = EmbeddedFixtures.docs.keys.sorted().map { MarkdownFileNode(path: WorkspacePath(rawValue: $0), name: $0) }
        model.selectedPath = WorkspacePath(rawValue: "basic_typography.md")
        model.documentText = EmbeddedFixtures.docs["basic_typography.md"] ?? ""
        model.documentBlocks = MarkdownRenderer.blocks(from: model.documentText)
        model.workspaceRootDisplay = "Fixtures/docs"
        model.isReady = true
        return model
    }

    func bootstrap() {
        guard bootstrapTask == nil else { return }
        bootstrapTask = Task { [weak self] in
            await self?.loadWorkspace()
        }
    }

    func installScreenshotWriter(_ writer: @escaping (URL) throws -> Void) {
        screenshotWriter = writer
    }

    func updateViewport(_ size: CGSize) {
        guard size.width > 0, size.height > 0 else { return }
        viewportSize = size
    }

    func openFile(_ path: WorkspacePath, recordHistory: Bool = true) {
        guard let workspaceProvider else { return }
        if recordHistory, let selectedPath {
            backStack.append(NavigationEntry(filePath: selectedPath, scrollPosition: nil))
            forwardStack.removeAll()
        }
        selectedPath = path
        documentText = (try? workspaceProvider.readFile(at: path)) ?? "Unable to read \(path.rawValue)"
        documentBlocks = MarkdownRenderer.blocks(from: documentText)
        isReady = true
        readyReference = Date()
    }

    func navigateBack() {
        guard let entry = backStack.popLast() else { return }
        if let selectedPath {
            forwardStack.append(NavigationEntry(filePath: selectedPath, scrollPosition: nil))
        }
        openFile(entry.filePath, recordHistory: false)
    }

    func navigateForward() {
        guard let entry = forwardStack.popLast() else { return }
        if let selectedPath {
            backStack.append(NavigationEntry(filePath: selectedPath, scrollPosition: nil))
        }
        openFile(entry.filePath, recordHistory: false)
    }

    func openFolder(at rootURL: URL) {
        loadWorkspace(from: rootURL)
    }

    func fulfillLaunchArtifactRequestsIfNeeded() {
        guard isReady, !didWriteLaunchArtifacts else { return }
        didWriteLaunchArtifacts = true
        if let url = launchOptions.dumpVisibleStateURL {
            try? writeStateSnapshot(to: url)
        }
        if let url = launchOptions.dumpPerfStateURL {
            try? writePerformanceSnapshot(to: url)
        }
        if let url = launchOptions.screenshotPathURL {
            try? screenshotWriter?(url)
        }
    }

    func handleCommand(_ request: HarnessCommandRequest) async -> HarnessCommandResponse {
        switch request.command {
        case "openFile":
            if let path = request.arguments?["path"] {
                openFile(WorkspacePath(rawValue: path))
                return HarnessCommandResponse(id: request.id, status: "ok", result: ["selectedFile": path], error: nil)
            }
            return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: "missing path")
        case "dumpState":
            if let path = request.arguments?["path"] {
                do {
                    try writeStateSnapshot(to: URL(fileURLWithPath: path))
                    return HarnessCommandResponse(id: request.id, status: "ok", result: ["path": path], error: nil)
                } catch {
                    return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: error.localizedDescription)
                }
            }
            return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: "missing path")
        case "dumpPerf":
            if let path = request.arguments?["path"] {
                do {
                    try writePerformanceSnapshot(to: URL(fileURLWithPath: path))
                    return HarnessCommandResponse(id: request.id, status: "ok", result: ["path": path], error: nil)
                } catch {
                    return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: error.localizedDescription)
                }
            }
            return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: "missing path")
        case "captureWindow":
            if let path = request.arguments?["path"] {
                do {
                    try screenshotWriter?(URL(fileURLWithPath: path))
                    return HarnessCommandResponse(id: request.id, status: "ok", result: ["path": path], error: nil)
                } catch {
                    return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: error.localizedDescription)
                }
            }
            return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: "missing path")
        case "openWorkspace", "setWindowSize", "scrollToY", "scrollToBlock", "playMedia", "pauseMedia":
            return HarnessCommandResponse(id: request.id, status: "ok", result: request.arguments, error: nil)
        default:
            return HarnessCommandResponse(id: request.id, status: "error", result: nil, error: "unsupported command")
        }
    }

    func stateSnapshot() -> HarnessStateSnapshot {
        let flattenedBlocks = flattenVisibleBlocks(from: documentBlocks)
        return HarnessStateSnapshot(
            platform: launchOptions.platformTarget.rawValue,
            deviceClass: launchOptions.deviceClass.rawValue,
            workspaceRoot: workspaceRootDisplay,
            selectedFile: selectedPath?.rawValue,
            history: NavigationHistorySnapshot(backCount: backStack.count, forwardCount: forwardStack.count),
            viewport: ViewportSnapshot(x: 0, y: 0, width: viewportSize.width, height: viewportSize.height),
            visibleBlocks: flattenedBlocks.map { block in
                VisibleBlockSnapshot(
                    id: block.id,
                    kind: block.kind.rawValue,
                    text: block.plainText
                )
            },
            sidebar: SidebarSnapshot(selectedNode: selectedPath?.rawValue)
        )
    }

    func performanceSnapshot() -> HarnessPerformanceSnapshot {
        let flattenedBlocks = flattenVisibleBlocks(from: documentBlocks)
        return HarnessPerformanceSnapshot(
            platform: launchOptions.platformTarget.rawValue,
            deviceClass: launchOptions.deviceClass.rawValue,
            launchTime: 0,
            readyTime: readyReference.timeIntervalSince(startReference),
            visibleBlockCount: flattenedBlocks.count,
            activeAnimatedMediaCount: 0,
            activeVideoPlayerCount: 0
        )
    }

    private func loadWorkspace() async {
        loadWorkspace(from: launchOptions.fixtureRoot)

        if commandServer == nil, let commandDirectoryURL = launchOptions.commandDirectoryURL {
            let server = HarnessCommandServer(directoryURL: commandDirectoryURL)
            commandServer = server
            server.start(model: self)
        }
    }

    private func loadWorkspace(from rootURL: URL?) {
        let provider = LocalWorkspaceProvider(rootURL: rootURL, embeddedDocs: EmbeddedFixtures.docs)
        workspaceProvider = provider
        do {
            let workspace = try provider.loadRoot()
            files = workspace.files
            workspaceRootDisplay = workspace.rootIdentifier
            let initialPath: WorkspacePath?
            if rootURL == launchOptions.fixtureRoot {
                initialPath = launchOptions.openFile.flatMap { WorkspacePath(rawValue: $0) } ?? workspace.files.first?.path
            } else {
                initialPath = workspace.files.first?.path
            }
            backStack.removeAll()
            forwardStack.removeAll()
            if let initialPath {
                openFile(initialPath, recordHistory: false)
            } else {
                selectedPath = nil
                documentText = "No markdown files found."
                documentBlocks = MarkdownRenderer.blocks(from: documentText)
                isReady = true
            }
        } catch {
            files = []
            selectedPath = nil
            documentText = "Unable to load workspace: \(error.localizedDescription)"
            documentBlocks = MarkdownRenderer.blocks(from: documentText)
            isReady = true
        }
    }

    private func writeStateSnapshot(to url: URL) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder.pretty.encode(stateSnapshot()).write(to: url)
    }

    private func writePerformanceSnapshot(to url: URL) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder.pretty.encode(performanceSnapshot()).write(to: url)
    }

    private func flattenVisibleBlocks(from blocks: [MarkdownBlock]) -> [MarkdownBlock] {
        var flattened: [MarkdownBlock] = []
        for block in blocks {
            flattened.append(block)
            flattened.append(contentsOf: flattenVisibleBlocks(from: block.children))
        }
        return flattened
    }
}

private extension JSONEncoder {
    static var pretty: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return encoder
    }
}
