//
//  Swift_Markdown_ViewerApp.swift
//  Swift Markdown Viewer
//
//  Created by Matthew Moore on 3/19/26.
//

import SwiftUI
#if os(macOS)
import AppKit
#endif

@main
struct Swift_Markdown_ViewerApp: App {
    @StateObject private var model = AppModel(launchOptions: HarnessLaunchOptions.fromProcess())

    var body: some Scene {
        WindowGroup {
            ContentView(model: model)
        }
        #if os(macOS)
        .commands {
            CommandGroup(after: .newItem) {
                Divider()
                Button("Open Folder…") {
                    openFolder()
                }
                .keyboardShortcut("o", modifiers: [.command])
            }
        }
        #endif
    }

    #if os(macOS)
    private func openFolder() {
        if model.launchOptions.uiTestMode, let testFolderURL = model.launchOptions.uiTestOpenFolderURL {
            model.openFolder(at: testFolderURL)
            return
        }

        let panel = NSOpenPanel()
        panel.title = "Open Folder"
        panel.prompt = "Open"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = false
        panel.allowsMultipleSelection = false

        guard panel.runModal() == .OK, let selectedURL = panel.url else {
            return
        }

        model.openFolder(at: selectedURL)
    }
    #endif
}
