//
//  Swift_Markdown_ViewerApp.swift
//  Swift Markdown Viewer
//
//  Created by Matthew Moore on 3/19/26.
//

import SwiftUI

@main
struct Swift_Markdown_ViewerApp: App {
    private let launchOptions: HarnessLaunchOptions
    @StateObject private var sessionStore: WorkspaceWindowSessionStore

    init() {
        let resolvedLaunchOptions = HarnessLaunchOptions.fromProcess()
        launchOptions = resolvedLaunchOptions
        UITestOpenFolderSelectionStore.shared.configureIfNeeded(using: resolvedLaunchOptions)
        _sessionStore = StateObject(
            wrappedValue: WorkspaceWindowSessionStore(launchOptions: resolvedLaunchOptions)
        )
    }

    var body: some Scene {
        WindowGroup(for: String.self) { $sceneID in
            WindowSceneRootView(
                launchOptions: launchOptions,
                sceneID: sceneID,
                sessionStore: sessionStore
            )
        } defaultValue: {
            UUID().uuidString
        }
        #if os(macOS)
        .commands {
            WindowOpenFolderCommands()
        }
        #endif
    }
}
