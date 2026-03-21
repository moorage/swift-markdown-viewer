//
//  Swift_Markdown_ViewerUITests.swift
//  Swift Markdown ViewerUITests
//
//  Created by Matthew Moore on 3/19/26.
//

import XCTest

final class Swift_Markdown_ViewerUITests: XCTestCase {

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testSmokeLaunchShowsHarnessShell() throws {
        let app = XCUIApplication()
        let repoRoot = ProcessInfo.processInfo.environment["PWD"] ?? FileManager.default.currentDirectoryPath
        let fixtureRoot = "\(repoRoot)/Fixtures/docs"
        app.launchArguments = [
            "--fixture-root", fixtureRoot,
            "--open-file", "basic_typography.md",
            "--ui-test-mode", "1",
        ]
        app.launch()

        XCTAssertTrue(app.buttons["nav.back"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["nav.forward"].exists)
        XCTAssertTrue(app.staticTexts["nav.title"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.scrollViews["document.scrollView"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testOpenFolderCommandUpdatesSidebarAndTitle() throws {
        let app = XCUIApplication()
        let repoRoot = ProcessInfo.processInfo.environment["PWD"] ?? FileManager.default.currentDirectoryPath
        let initialFixtureRoot = "\(repoRoot)/Fixtures/docs"
        let selectedFolder = try makeWorkspace(named: "UITest Workspace", files: [
            "zeta.md": "# Zeta\n\nOpened from UI test."
        ])

        app.launchArguments = [
            "--fixture-root", initialFixtureRoot,
            "--open-file", "basic_typography.md",
            "--ui-test-open-folder", selectedFolder.path,
            "--ui-test-mode", "1",
        ]
        app.launch()

        XCTAssertTrue(app.staticTexts["nav.title"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Fixtures/docs > basic_typography.md"].exists)

        app.typeKey("o", modifierFlags: .command)

        let openedSidebarNode = app.buttons["sidebar.node.zeta.md"]
        XCTAssertTrue(openedSidebarNode.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["UITest Workspace > zeta.md"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testLaunchPerformance() throws {
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            let app = XCUIApplication()
            app.launch()
        }
    }

    private func makeWorkspace(named folderName: String, files: [String: String]) throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        let folder = root.appendingPathComponent(folderName, isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        for (path, contents) in files {
            let fileURL = folder.appendingPathComponent(path)
            try FileManager.default.createDirectory(at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            try contents.write(to: fileURL, atomically: true, encoding: .utf8)
        }
        return folder
    }
}
