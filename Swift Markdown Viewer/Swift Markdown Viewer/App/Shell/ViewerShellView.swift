import SwiftUI

struct ViewerShellView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        NavigationSplitView {
            List(model.files) { file in
                Button {
                    model.openFile(file.path)
                } label: {
                    HStack {
                        Text(file.name)
                            .font(.body)
                        Spacer()
                        if model.selectedPath == file.path {
                            Image(systemName: "checkmark")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier(AccessibilityIDs.sidebarNode(file.path.rawValue))
            }
            .listStyle(.sidebar)
            .accessibilityIdentifier(AccessibilityIDs.sidebarList)
        } detail: {
            detailContent
        }
        #if os(macOS)
        .toolbar {
            ToolbarItem(placement: .navigation) {
                macNavigationControls
            }
        }
        .background(MacWindowConfiguration(title: model.windowTitle, contentSize: model.launchOptions.windowSize))
        #endif
    }

    private var detailContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ForEach(model.documentBlocks) { block in
                    MarkdownBlockView(block: block)
                }
            }
                .frame(maxWidth: .infinity, alignment: .leading)
                .textSelection(.enabled)
                .accessibilityIdentifier(AccessibilityIDs.text)
                .padding(.bottom, 24)
        }
        .accessibilityIdentifier(AccessibilityIDs.scrollView)
        .padding(20)
        #if os(macOS)
        .overlay(alignment: .topLeading) {
            Text(model.windowTitle)
                .accessibilityIdentifier(AccessibilityIDs.title)
                .hidden()
        }
        #endif
        #if !os(macOS)
        .safeAreaInset(edge: .top) {
            HStack(spacing: 12) {
                Button(action: model.navigateBack) {
                    Label("Back", systemImage: "chevron.left")
                }
                .disabled(!model.canNavigateBack)
                .accessibilityIdentifier(AccessibilityIDs.backButton)

                Button(action: model.navigateForward) {
                    Label("Forward", systemImage: "chevron.right")
                }
                .disabled(!model.canNavigateForward)
                .accessibilityIdentifier(AccessibilityIDs.forwardButton)

                Text(model.windowTitle)
                    .font(.headline)
                    .lineLimit(1)
                    .accessibilityIdentifier(AccessibilityIDs.title)

                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.top, 8)
        }
        #endif
    }

    #if os(macOS)
    private var macNavigationControls: some View {
        ControlGroup {
            Button(action: model.navigateBack) {
                Image(systemName: "chevron.left")
            }
            .disabled(!model.canNavigateBack)
            .accessibilityIdentifier(AccessibilityIDs.backButton)
            .help("Back")

            Button(action: model.navigateForward) {
                Image(systemName: "chevron.right")
            }
            .disabled(!model.canNavigateForward)
            .accessibilityIdentifier(AccessibilityIDs.forwardButton)
            .help("Forward")
        }
        .controlGroupStyle(.navigation)
        .labelStyle(.iconOnly)
    }
    #endif
}

private struct MarkdownBlockView: View {
    let block: MarkdownBlock

    var body: some View {
        switch block.kind {
        case .heading:
            Text(MarkdownRenderer.attributedText(for: block))
                .font(headingFont(for: block.level ?? 1))
                .fontWeight(.semibold)
        case .paragraph:
            Text(MarkdownRenderer.attributedText(for: block))
                .font(.body)
        case .unorderedListItem:
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top, spacing: 10) {
                    Text(listMarker)
                    Text(MarkdownRenderer.attributedText(for: block))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                if !block.children.isEmpty {
                    childBlocks
                }
            }
            .padding(.leading, CGFloat(block.indentLevel) * 18)
        case .orderedListItem:
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top, spacing: 10) {
                    Text(listMarker)
                        .monospacedDigit()
                    Text(MarkdownRenderer.attributedText(for: block))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                if !block.children.isEmpty {
                    childBlocks
                }
            }
            .padding(.leading, CGFloat(block.indentLevel) * 18)
        case .blockquote:
            HStack(alignment: .top, spacing: 12) {
                Rectangle()
                    .fill(.quaternary)
                    .frame(width: 4)
                Text(MarkdownRenderer.attributedText(for: block))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        case .codeBlock:
            ScrollView(.horizontal, showsIndicators: false) {
                Text(verbatim: block.sourceText)
                    .font(.system(.body, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(14)
            }
            .background(Color.secondary.opacity(0.08))
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        case .table:
            if let table = block.table {
                ScrollView(.horizontal, showsIndicators: false) {
                    Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 10) {
                        GridRow {
                                ForEach(Array(table.header.enumerated()), id: \.offset) { column, cell in
                                Text(MarkdownRenderer.attributedText(for: cell))
                                    .fontWeight(.semibold)
                                    .frame(maxWidth: .infinity, alignment: alignment(for: table.alignments[column]))
                            }
                        }
                        Divider()
                            .gridCellColumns(table.header.count)
                        ForEach(Array(table.rows.enumerated()), id: \.offset) { _, row in
                            GridRow {
                                    ForEach(Array(row.enumerated()), id: \.offset) { column, cell in
                                    Text(MarkdownRenderer.attributedText(for: cell))
                                        .frame(maxWidth: .infinity, alignment: alignment(for: table.alignments[column]))
                                }
                            }
                        }
                    }
                    .padding(14)
                }
                .background(Color.secondary.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .stroke(Color.secondary.opacity(0.15), lineWidth: 1)
                )
            }
        case .image:
            if let image = block.image {
                VStack(alignment: .leading, spacing: 8) {
                    Label(image.altText.isEmpty ? "Image" : image.altText, systemImage: "photo")
                        .font(.headline)
                    Text(image.sourceURL)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let title = image.title, !title.isEmpty {
                        Text(title)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(14)
                .background(Color.secondary.opacity(0.06))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            }
        case .rawHTML:
            Text(verbatim: block.sourceText)
                .font(.system(.body, design: .monospaced))
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(14)
                .background(Color.secondary.opacity(0.06))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        case .thematicBreak:
            Divider()
                .padding(.vertical, 4)
        }
    }

    private func headingFont(for level: Int) -> Font {
        switch level {
        case 1:
            return .system(size: 30, weight: .semibold, design: .default)
        case 2:
            return .system(size: 24, weight: .semibold, design: .default)
        case 3:
            return .system(size: 20, weight: .semibold, design: .default)
        default:
            return .headline
        }
    }

    private var listMarker: String {
        if block.isTaskItem {
            return block.isTaskCompleted == true ? "\u{2611}" : "\u{2610}"
        }
        if block.kind == .orderedListItem {
            return "\(block.listItemIndex ?? 1)."
        }
        return "\u{2022}"
    }

    @ViewBuilder
    private var childBlocks: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(block.children) { child in
                MarkdownBlockView(block: child)
            }
        }
        .padding(.leading, 28)
    }

    private func alignment(for alignment: MarkdownTableAlignment) -> Alignment {
        switch alignment {
        case .leading:
            return .leading
        case .center:
            return .center
        case .trailing:
            return .trailing
        }
    }
}
