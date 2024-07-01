# Tidy XML for digital editions

This script is used to transform the formatting of XML documents into tidier form. It’s first and foremost tailored for documents exported from [Transkribus](https://www.transkribus.org/), but can also be used for documents converted from word processor documents with [TEIGarage Conversion](https://teigarage.tei-c.org/).

The script can also add expansions to unexpanded abbreviations in the documents from a separate JSON file. This can be done either to abbreviations encoded as `<choice><abbr>Abbr</abbr><expan/></choice>` or abbreviations that have not been encoded at all (option `CHECK_UNTAGGED_ABBREVIATIONS`, see below).

Created by Sebastian Köhler in April and June 2024 on the basis of a script by Anna Movall (<https://github.com/Movanna/transform_texts/blob/main/transform_xml.py>).


## Installation in order to run the script from the command line

### 1. Clone the repository

Use [GitHub Desktop](https://desktop.github.com/), or open a terminal window and run the following [git](https://www.git-scm.com/) command:

```bash
git clone git@github.com:slsfi/digital-edition-tidy-xml-py.git
```

### 2. In a terminal window, navigate into the project directory

```bash
cd /path/to/digital-edition-tidy-xml-py
```

### 3. Set up a virtual environment for the script

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


## Running the app from the command line

- Add the xml-files which are to be tidied in a folder named `bad_xml` in the same folder as the script file `tidy_xml.py`. The xml-files should be encoded according to the [TEI standard](https://tei-c.org/). If exporting xml-files from Transkribus, the tag lines TEI export option must be set to `<lb/>` for all texts except poetry. For poetry, set the tag lines export option to `<l>...</l>`.
- Optionally add `abbr_dictionary.json` to a folder named `dictionaries` in the same folder as the script file. The JSON-file should contain abbreviations and their expansions as key–value pairs in JSON format.
- Rename `.env_example` -> `.env` and modify the parameters if necessary (see parameters below).

`.env` file parameters:

- `CHECK_UNTAGGED_ABBREVIATIONS`: `True`/`False`. When `True` and a dictionary file containing abbrevations and their expansions is available, untagged abbreviations are searched for and encoded. Defaults to `False`.
- `EXCLUDE_RANGE_NUMBERS_NORMALIZATION`: String. A min and max value defining a range of numbers which are excluded from normalization of the thousand separator. Typically some values which are years should not have a thousand separator. Defaults to `1500-1900`.
- `NORMALIZE_LARGE_NUMBERS`: `True`/`False`. When `True`, a thousand separator is inserted in all numbers above 999 and existing separators are normalized. Defaults to `True`.
- `NORMALIZED_THOUSAND_SEPARATOR`: String. The character or string to use as the thousand separator in normalized numbers above 999. Defaults to the narrow no-break space character `&#x202F;`.
- `PRESERVE_LB_TAGS`: `True`/`False`. When `True`, line beginning tags `<lb/>` are preserved in the output, when `False` they are mostly stripped. Defaults to `False`. Should only be set to `True` if the “bad” XML has been exported from Transkribus with the tag lines TEI export option set to `<lb/>` and each `<lb/>` should be preserved.
- `REG_ENCODE_NUMBERS_NORMALIZATION`: `True`/`False`. When `True`, normalized numbers are enclosed in `<reg>` tags. Defaults to `False`.

Output: Tidied xml-files in a folder named `good_xml` in the same folder as the script file.

Command line arguments: No arguments.


## Building an executable with pyinstaller

First, set `EXE_MODE` to `True` in `tidy_xml.py`.

Then run:

```bash
pyinstaller tidy_xml.py --onefile --clean --name tidy_xml_x.y.z
```

where `x.y.z` should be replaced with the actual semantic version number of the script.

Your bundled application should now be available in the `dist` folder.


## Change log

- 2024-07-01: v1.0.0
