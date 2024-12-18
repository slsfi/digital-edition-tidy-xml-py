# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## 1.1.0 – 2024-12-18

### Added

- Support for UTF-8-BOM encoded xml-files.
- Support for handling XML documents without the body-element.
- Support for handling blockquotes.
- Support for small caps `@rend` values.

### Changed

- Ensure line breaks in output XML before p-elements.
- Deps: update `lxml` to 5.3.0.
- Deps: update `pyinstaller` to 6.11.1.

### Fixed

- head-element attributes.
- Superscript attribute value for `@rend`.



## 1.0.0 – 2024-07-01

Initial release.
