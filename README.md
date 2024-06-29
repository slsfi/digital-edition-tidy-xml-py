# Tidy XML for digital editions

This script is used to transform the formatting of XML documents into tidier form. It’s first and foremost tailored for documents exported from Transkribus, but can also be used for documents converted from word processor documents with TEIGarage Conversion.

The script can also add expansions to unexpanded abbreviations in the documents from a separate JSON file. This can be done either to abbreviations encoded as `<choice><abbr>Abbr</abbr><expan/></choice>` or abbreviations that have not been encoded at all (option CHECK_UNTAGGED_ABBREVIATIONS, see below).

Created by Sebastian Köhler 2024-06-26 on the basis of a script by Anna Movall (https://github.com/Movanna/transform_texts/blob/main/transform_xml.py).

## Change log

- 2024-06-26: v1.0.0

## Installation

### 1. Clone the repository

Use [GitHub Desktop](https://desktop.github.com/), or open a terminal window and run the following [git](https://www.git-scm.com/) command:

```bash
git clone git@github.com:slsfi/digital-edition-tidy-xml-py.git
```

### 2. In a terminal window, navigate into the project directory

```bash
cd /path/to/digital-edition-tidy-xml-py
```

### 3. Set up a virtual environment

```bash
python -m venv venv-tidy-xml
```

### 4. Activate the virtual environment

On Windows, run:
```bash
venv-tidy-xml\Scripts\activate
```

On Unix or macOS, run:
```bash
source venv-tidy-xml/bin/activate
```

### 5. Install required dependencies
```bash
pip install -r requirements.txt
```


## Running the app

- Add the xml-files which are to be tidied in a folder named `bad_xml` in the same folder as this script file.
- Optionally add `abbr_dictionary.json` to a folder named `dictionaries` in the same folder as this script file. The file should contain abbreviations and their expansions as key–value pairs in JSON format.
- Rename .env_example -> .env and modify the parameters if necessary.

`.env` file parameters:

- `NORMALIZE_LARGE_NUMBERS`: True/False. When True, a thousand separator is inserted in all numbers above 999 and existing separators are normalized. Defaults to True.
- `NORMALIZED_THOUSAND_SEPARATOR`: Text. The character or string to use as the thousand separator in normalized numbers above 999. Defaults to the narrow no-break space character `&#x202F;`.
- `EXCLUDE_RANGE_NUMBERS_NORMALIZATION`: Text. A min and max value defining a range of numbers which are excluded from normalization of the thousand separator. Typically some values which are years should not have a thousand separator. Defaults to `1500-1900`.
- `REG_ENCODE_NUMBERS_NORMALIZATION`: True/False. When True, normalized numbers are enclosed in `<reg>` tags. Defaults to False.
- `CHECK_UNTAGGED_ABBREVIATIONS`: True/False. When True and a dictionary file containing abbrevations and their expansions is available, untagged abbreviations are searched for and encoded. Defaults to `False`.
- `PRESERVE_LB_TAGS`: True/False. When True, line beginning tags <lb/> are preserved in the output, when False they are stripped.

Output: Tidied xml-files in a folder named `good_xml` relative to this script file.

Command line arguments: No arguments.

## Building an executable with pyinstaller

Run:

```bash
pyinstaller tidy_xml.py --onefile --clean --name tidy_xml_x.y.z
```

where `x.y.z` should be replaced with the actual semantic version number of the script.

Your bundled application should now be available in the `dist` folder.
