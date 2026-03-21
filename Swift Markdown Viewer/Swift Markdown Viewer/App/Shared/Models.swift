import Foundation

struct WorkspacePath: Hashable, Codable, Identifiable {
    let rawValue: String

    var id: String { rawValue }
}

struct MarkdownFileNode: Identifiable, Hashable {
    let path: WorkspacePath
    let name: String

    var id: String { path.rawValue }
}

struct Workspace {
    let rootIdentifier: String
    let files: [MarkdownFileNode]
}

struct NavigationEntry: Equatable {
    let filePath: WorkspacePath
    let scrollPosition: Double?
}

enum MarkdownBlockKind: String, Hashable {
    case heading
    case paragraph
    case unorderedListItem
    case orderedListItem
    case blockquote
    case codeBlock
    case table
    case image
    case rawHTML
    case thematicBreak
}

enum MarkdownTableAlignment: String, Hashable {
    case leading
    case center
    case trailing
}

struct MarkdownTable: Hashable {
    let alignments: [MarkdownTableAlignment]
    let header: [String]
    let rows: [[String]]
}

struct MarkdownImage: Hashable {
    let altText: String
    let sourceURL: String
    let title: String?
}

struct MarkdownBlock: Identifiable, Hashable {
    let id: String
    let kind: MarkdownBlockKind
    let plainText: String
    let sourceText: String
    let level: Int?
    let listItemIndex: Int?
    let indentLevel: Int
    let isTaskItem: Bool
    let isTaskCompleted: Bool?
    let table: MarkdownTable?
    let image: MarkdownImage?
    let attributedText: AttributedString?
    let children: [MarkdownBlock]
}
