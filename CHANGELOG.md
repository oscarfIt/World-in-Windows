# Changelog

All notable changes to World in Windows will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Edit buttons and functionality to Spell, Item, Condition, and Location Detail windows
- Functionality to open LocationDetailWindow from main window

### Changed
- Changes to existing features

### Fixed
- Bug fixes

### Removed
- IDs from Locations and NPCs

## [1.2.1] - 2025-11-10

### Fixed
- Erroneous __release_name__ import in main_window.py

## [1.2.0] - 2025-11-10
### Added
- Add functionality for all Browse Dialogs (Spell, Item, Condition, Location)

## [1.1.0] - 2025-11-10
### Added
- Initial release
- Location tree view with nested locations
- NPC management system
- Spell, item, and class action browsers
- Knowledge base with automatic linking
- PC Class stat blocks with ability scores
- Location detail windows
- NPC detail windows with stat blocks
- Campaign notes for NPCs
- Search and filter functionality
- D&D themed UI styling
- Data refresh functionality
- PyQt6-based GUI

### Features
- Browse locations in hierarchical tree structure
- View NPCs associated with locations
- Double-click to open detail windows
- Clickable cross-references between game elements
- Support for Monster Manual stat blocks
- Support for PC Class stat blocks
- Image support for entries
- Configurable data and media paths

---

## Version Numbering Guide

We use [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible changes (e.g., data format changes requiring migration)
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

## Release Names

Each major/minor release gets a D&D themed name:
- 1.0.0: "Beholder's Eye"
- Future examples: "Dragon's Hoard", "Lich's Phylactery", "Tarrasque Awakens"
