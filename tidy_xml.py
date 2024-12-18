import json
import os
import re
import sys

from bs4 import BeautifulSoup
from dotenv import load_dotenv


SCRIPT_VERSION = "1.1.0"

# Flag for additional console output while running the script,
# intended to be set to True when building an executable using
# pyinstaller.
EXE_MODE = True

# Flag for running the script in debug mode, which outputs the
# processed xml after parsing and during tidying.
DEBUG = False

SOURCE_FOLDER = "bad_xml"
OUTPUT_FOLDER = "good_xml"
ABBR_DICT_FILEPATH = "dictionaries/abbr_dictionary.json"

# Load parameters from .env file
load_dotenv()

if os.getenv("NORMALIZE_LARGE_NUMBERS") == "False":
	NORMALIZE_LARGE_NUMBERS = False
else:
	NORMALIZE_LARGE_NUMBERS = True

if os.getenv("NORMALIZED_THOUSAND_SEPARATOR") != "" and os.getenv("NORMALIZED_THOUSAND_SEPARATOR") is not None:
	NORMALIZED_THOUSAND_SEPARATOR = os.getenv("NORMALIZED_THOUSAND_SEPARATOR")
else:
	NORMALIZED_THOUSAND_SEPARATOR = "&#x202F;"

if os.getenv("EXCLUDE_RANGE_NUMBERS_NORMALIZATION") != "" and os.getenv("EXCLUDE_RANGE_NUMBERS_NORMALIZATION") is not None and "-" in os.getenv("EXCLUDE_RANGE_NUMBERS_NORMALIZATION"):
	exclude_parts = os.getenv("EXCLUDE_RANGE_NUMBERS_NORMALIZATION").split("-")
	if exclude_parts[0].isdigit():
		EXCLUDE_NUMBERS_NORM_MIN = int(exclude_parts[0])
	else:
		EXCLUDE_NUMBERS_NORM_MIN = 1500
	if len(exclude_parts) > 1 and exclude_parts[1].isdigit():
		EXCLUDE_NUMBERS_NORM_MAX = int(exclude_parts[1])
	else:
		EXCLUDE_NUMBERS_NORM_MAX = 1900
else:
	EXCLUDE_NUMBERS_NORM_MIN = -1
	EXCLUDE_NUMBERS_NORM_MAX = -1

if os.getenv("REG_ENCODE_NUMBERS_NORMALIZATION") == "True":
	REG_ENCODE_NUMBERS_NORMALIZATION = True
else:
	REG_ENCODE_NUMBERS_NORMALIZATION = False

# if True: look for unencoded abbreviations and
# surround them with the needed tags as well as
# add the likely expansions
if os.getenv("CHECK_UNTAGGED_ABBREVIATIONS") == "True":
	CHECK_UNTAGGED_ABBREVIATIONS = True
else:
	CHECK_UNTAGGED_ABBREVIATIONS = False

if os.getenv("PRESERVE_LB_TAGS") == "True":
	PRESERVE_LB_TAGS = True
else:
	PRESERVE_LB_TAGS = False


def main():
	if EXE_MODE:
		print_exe_header()

	# Check if the source folder exists
	if not os.path.exists(SOURCE_FOLDER):
		print(f"\nError: The input folder '{SOURCE_FOLDER}' does not exist. Please create it in the same folder as the script and rerun the script.")
		if EXE_MODE:
			input("\nPress Enter to close this window ")
		sys.exit(1)

	file_list = get_source_file_paths()

	if len(file_list) > 0:
		# Ensure the output directory exists
		os.makedirs(OUTPUT_FOLDER, exist_ok=True)
	else:
		print(f"\nError: There are no xml-files to process in the input folder '{SOURCE_FOLDER}/'.")
		if EXE_MODE:
			input("\nPress Enter to close this window ")
		sys.exit(1)

	abbr_dictionary = read_dict_from_file(ABBR_DICT_FILEPATH)

	if EXE_MODE:
		print()
		input("Press Enter to start processing xml-files ")

	file_list_len = len(file_list)
	print(f"\nProcessing {file_list_len} XML-files:")

	n: int = 0
	for file in file_list:
		n += 1
		print(f"{n}/{file_list_len}: ", flush=True, end="")

		old_soup: BeautifulSoup = read_xml(file)
		new_soup: BeautifulSoup = transform_xml(old_soup, abbr_dictionary)

		if DEBUG:
			write_to_file(str(new_soup), f"parsing_temp_{n}.xml")

		tidy_xml_string: str = tidy_up_xml(str(new_soup), abbr_dictionary, n)
		write_to_file(tidy_xml_string, file)
		print(f"Created {OUTPUT_FOLDER}/{file}")

	print(f"\nSuccessfully tidied {len(file_list)} XML-files.\n")

	if EXE_MODE:
		input("Press Enter to close this window ")


# loop through xml source files in folder and append to list
def get_source_file_paths():
	file_list = []
	for filename in os.listdir(SOURCE_FOLDER):
		if filename.endswith(".xml"):
			file_list.append(filename)
	return file_list


# read an xml file and return its content as a soup object
def read_xml(filename) -> BeautifulSoup:
	with open (SOURCE_FOLDER + "/" + filename, "r", encoding="utf-8-sig") as source_file:
		file_content = source_file.read()
		old_soup = BeautifulSoup(file_content, "xml")
	return old_soup


# get dictionary content from file
def read_dict_from_file(filename):
	try:
		with open(filename, encoding="utf-8-sig") as source_file:
			json_content = json.load(source_file)
			return json_content
	except FileNotFoundError as error:
		print(f"Info: Dictionary file for abbreviations not found in path\n      '{ABBR_DICT_FILEPATH}'.")
		print("      Expansions to unexpanded abbreviations will not be added.")
		return {}


def transform_xml(old_soup: BeautifulSoup, abbr_dictionary) -> BeautifulSoup:
	"""Transforms certain elements, attributes and values in old_soup, which is a BeautifulSoup object, and returns the transformed BeautifulSoup object."""
	# Create a new soup with <root>
	new_soup: BeautifulSoup = BeautifulSoup("<root></root>", "xml")

	# Find the <body> or root element
	xml_body = old_soup.find("body")
	if xml_body is None:
		# No <body> element in XML document, get root element instead
		old_root = old_soup.find()
		old_root.name = "body"
		new_soup.root.append(old_root)
	else:
		# Append <body> if it already exists
		new_soup.root.append(xml_body)
	
	# Unwrap <body> to move its contents directly into <root>
	new_soup.body.unwrap()

	# get all <anchor/> and remove them
	anchors = new_soup.find_all("anchor")
	for anchor in anchors:
		anchor.unwrap()
	# get all <pb>, remove @facs and @xml:id, add @type="orig"
	pbs = new_soup.find_all("pb")
	for pb in pbs:
		if "facs" in pb.attrs:
			del pb["facs"]
		if "xml:id" in pb.attrs:
			del pb["xml:id"]
		pb["type"] = "orig"
	# get all <p>, remove @facs and @style
	ps = new_soup.find_all("p")
	for p in ps:
		# Check if <p> contains only an <lg> element
		if p.lg:
			# Replace the <p> element with its <lg> child
			p.replace_with(p.lg)
		else:
			if "facs" in p.attrs:
				del p["facs"]
			if "style" in p.attrs:
				del p["style"]
			if "rend" in p.attrs:
				value = p["rend"]
				if value == "Quote":
					# Wrap the element in <quote type="block">
					p.wrap(new_soup.new_tag("quote", attrs={"type": "block"}))
					del p["rend"]
				elif value == "footnote text":
					p.unwrap()
				else:
					del p["rend"]
	# get all <note>
	notes = new_soup.find_all("note")
	for note in notes:
		if len(note.contents) == 1 and note.contents[0].name == "p":
			note.p.unwrap()
	# get all <l> and remove any @rend="indent" from them
	ls = new_soup.find_all("l")
	for l in ls:
		if "rend" in l.attrs:
			if l["rend"] == "indent":
				del l["rend"]
	# get all <lb/>, remove @facs and @n
	lbs = new_soup.find_all("lb")
	for lb in lbs:
		if "facs" in lb.attrs:
			del lb["facs"]
		if "n" in lb.attrs:
			del lb["n"]
	# get all <table>
	tables = new_soup.find_all("table")
	for table in tables:
		if "rend" in table.attrs:
			del table["rend"]
	# get all <cell>
	cells = new_soup.find_all("cell")
	for cell in cells:
		if "style" in cell.attrs:
			del cell["style"]
		if "rend" in cell.attrs:
			if "botBorder" not in cell["rend"] and "rightBorder" not in cell["rend"] and "bold" not in cell["rend"] and "center" not in cell["rend"] and "verticalCenter" not in cell["rend"]:
				del cell["rend"]
	# get all <list>
	lists = new_soup.find_all("list")
	for list in lists:
		if "type" in list.attrs:
			del list["type"]
		if "rend" in list.attrs:
			value = list["rend"]
			if value == "numbered":
				list["rend"] = "decimal"
	# get all <hi>
	his = new_soup.find_all("hi")
	for hi in his:
		if "style" in hi.attrs:
			del hi["style"]
		if "xml:space" in hi.attrs:
			del hi["xml:space"]
		# Check if the <hi> has exactly one child and it's a <seg> with rend="bold"
		if len(hi.contents) == 1 and hi.contents[0].name == "seg":
			rend_value = hi.contents[0].get("rend")
			if rend_value and ("bold" in rend_value or "italic" in rend_value):
				# Replace the <hi> element with its <seg> child
				hi.replace_with(hi.contents[0])
				continue
		if "rend" in hi.attrs:
			del hi["style"]
			value = hi["rend"]
			if "color" in value:
				pattern = re.compile(r"\s*color\(.*\)")
				value = pattern.sub("", value)
				if value == "":
					hi.unwrap()
					continue
				else:
					hi["rend"] = value
			if "italic" in value and "bold" in value:
				hi["rend"] = "bold italics"
			elif "underlined" in value:
				hi["rend"] = "underline"
			elif "super" in value:
				hi["rend"] = "superscript"
			elif "strikethrough" in value:
				del hi["rend"]
				hi.name = "tag"
			elif "italic" in value:
				hi["rend"] = "italics"
			elif value == "Emphasis":
				del hi["rend"]
			elif "Body" in value or "Other" in value or "Footnote" in value or "Table" in value or "Heading" in value:
				hi.unwrap()
				continue
	# get all <seg>
	segs = new_soup.find_all("seg")
	for seg in segs:
		if "xml:space" in seg.attrs:
			del seg["xml:space"]
		if "style" in seg.attrs:
			del seg["style"]
		if "rend" in seg.attrs:
			value = seg["rend"]
			if "italic" in value and "bold" in value:
				seg["rend"] = "bold italics"
				seg.name = "hi"
			elif "italic" in value:
				seg["rend"] = "italics"
				seg.name = "hi"
			elif "bold" in value:
				seg["rend"] = "bold"
				seg.name = "hi"
			elif "smallcaps" in value:
				seg["rend"] = "smallCaps"
				seg.name = "hi"
			else:
				seg.unwrap()
				continue
		if not seg.attrs:
			seg.unwrap()
			continue
	# get all <ref>
	refs = new_soup.find_all("ref")
	for ref in refs:
		if "target" in ref.attrs:
			ref["type"] = "readingtext"
			ref["target"] = ""
	# get all <ab>
	abs = new_soup.find_all("ab")
	for ab in abs:
		if "facs" in ab.attrs:
			del ab["facs"]
		if "type" in ab.attrs:
			del ab["type"]
	# get all <graphic>
	graphics = new_soup.find_all("graphic")
	for graphic in graphics:
		if "height" in graphic.attrs:
			del graphic["height"]
		if "width" in graphic.attrs:
			del graphic["width"]
		if "n" in graphic.attrs:
			del graphic["n"]
		if "rend" in graphic.attrs:
			del graphic["rend"]
	# get all <supplied>
	supplieds = new_soup.find_all("supplied")
	for supplied in supplieds:
		if "reason" in supplied.attrs:
			del supplied["reason"]
	# get all <comment>
	comments = new_soup.find_all("comment")
	for comment in comments:
		comment.name = "note"
	# get all <tag>
	tags = new_soup.find_all("tag")
	for tag in tags:
		if tag.string is not None and (str(tag.previous_element) == str("<del><tag>" + tag.string + "</tag></del>") or str(tag.next_element) == str("<del>" + tag.string + "</del>")):
			tag.unwrap()
		else:
			tag.name = "del"
	# get all <choice>
	choices = new_soup.find_all("choice")
	# it's easy to mark up abbreviations in Transkribus
	# this gets exported as <choice><abbr>Tit.</abbr><expan/></choice>
	# if we have a recorded expansion for the abbreviation:
	# add this expansion 
	# by handling one <choice> at a time we can get <abbr>
	# and <expan> as a pair
	for choice in choices:
		for child in choice.children:
			# we don't want to change <abbr> in any way,
			# we just need its content in order to check
			# the abbr_dictionary for a possible expansion
			if child.name == "abbr":
				abbr = child
				abbr_content = str(abbr)
				abbr_content = abbr_content.replace("<abbr>", "")
				abbr_content = abbr_content.replace("</abbr>", "")
				if abbr_content in abbr_dictionary.keys():
					expan_content = abbr_dictionary[abbr_content]
					# now get the <expan> to update
					for child in choice.children:
						# only add content to an empty <expan>
						if child.name == "expan" and len(child.contents) < 1:
							child.insert(0, expan_content)

	# Combine sibling <quote type="block"> elements
	new_soup = combine_quote_blocks(new_soup)

	return new_soup


# Get rid of tabs, extra spaces and newlines
# add newlines as preferred
# fix common problems caused by OCR programs, editors or
# otherwise present in source files
def tidy_up_xml(xml_string: str, abbr_dictionary, file_n: int):
	# Remove all whitespace characters at the beginning of lines,
 	# including blank lines
	pattern = re.compile(r"^\s+", re.MULTILINE)
	xml_string = pattern.sub("", xml_string)

	# Remove all carriage returns
	xml_string = xml_string.replace("\r", "")

	# Remove soft hyphen (U+00AD; &shy;) (invisible in VS Code)
	xml_string = xml_string.replace("­", "")

	# Replace no-break spaces with ordinary spaces
	xml_string = xml_string.replace(" ", " ")

	# Remove whitespace characters at the start or end of paragraph tags
	pattern = re.compile(r"<p>\s*")
	xml_string = pattern.sub("<p>", xml_string)
	pattern = re.compile(r"\s*</p>")
	xml_string = pattern.sub("</p>", xml_string)

	# Ensure all <lb/> start on new lines while processing
	xml_string = xml_string.replace("<p><lb/>", "<p>\n<lb/>")

	# Replace not signs to hyphens when followed by newlines
	xml_string = xml_string.replace("¬\n", "-\n")
	xml_string = xml_string.replace("¬<lb/>\n", "-<lb/>\n")

	# Replace hyphens with dashes when surrounded by combinations
	# of space, newline and <lb/>
	xml_string = xml_string.replace(" -\n", " –\n")
	xml_string = xml_string.replace(" -<lb/>", " –<lb/>")
	xml_string = xml_string.replace("\n- ", "\n– ")
	xml_string = xml_string.replace("<lb/>- ", "<lb/>– ")
	xml_string = xml_string.replace(" - ", " – ")

	# When there are several deleted lines of text,
	# exports from Transkribus contain one <del> per line,
	# but it's ok to have a <del> spanning several lines
	# so let's replace those chopped up <del>:s
	# the same goes for <add>
	xml_string = xml_string.replace("</del><lb/>\n<del>", "<lb/>\n")
	xml_string = xml_string.replace("</del>\n<lb/><del>", "\n<lb/>")
	xml_string = xml_string.replace("</add><lb/>\n<add>", "<lb/>\n")
	xml_string = xml_string.replace("</add>\n<lb/><add>", "\n<lb/>")

	# Remove lines that contain just <lb/> if followed by a line starting with <lb/>
	xml_string = xml_string.replace("\n<lb/>\n<lb/>", "\n<lb/>")

	# Let <hi> continue instead of being broken up into several <hi>:s.
	# We are assuming that the same @rend value continues on the second line.
	xml_string = re.sub(r"</hi>(\n<lb[^/]*?/>)<hi[^>]*?>", r"\1", xml_string)

	# Combine consecutive <hi rend="bold"> and <hi rend="italics"> tags
	attr_vals = ["bold", "italics"]
	for val in attr_vals:
		pattern = re.compile(fr'<hi rend="{val}">((?:(?!</hi>).)*)</hi><hi rend="{val}">((?:(?!</hi>).)*)</hi>')
		# While loop to repeatedly apply the replacement
		while pattern.search(xml_string):
			# Perform the substitution
			xml_string = pattern.sub(fr'<hi rend="{val}">\1\2</hi>', xml_string)
	
	# Move space character at the end of <hi> content outside closing tag
	xml_string = xml_string.replace(" </hi>", "</hi> ")

	# Output for debugging
	if DEBUG:
		write_to_file(xml_string, f"tidy_temp_{file_n}.xml")

	if PRESERVE_LB_TAGS:
		# Move any <lb/> tags at the end of lines to the start
		# and add attribute indicating hyphens if necessary
		xml_string = xml_string.replace("-<lb/>\n", '-\n<lb break="word"/>')
		xml_string = xml_string.replace("-\n<lb/>", '-\n<lb break="word"/>')
		xml_string = xml_string.replace("<lb/>\n", '\n<lb break="line"/>')
		xml_string = xml_string.replace("\n<lb/>", '\n<lb break="line"/>')
	else:
		# Remove hyphens followed by closing and opening <p> on new lines
		xml_string = xml_string.replace("-\n</p>\n<p>", "")
		# Remove hyphens followed by newlines and <lb/>
		xml_string = xml_string.replace("-\n<lb/>", "")
		xml_string = xml_string.replace("-\n", "")
		# Replace newline followed by <lb/> with space
		xml_string = xml_string.replace("\n<lb/>", " ")
		# Replace any remaining newlines with spaces within <p>
		xml_string = re.sub(r"<p>.*?</p>", newlines_to_spaces, xml_string, flags=re.DOTALL)
		# Remove multiple consecutive whitespace characters within <p>
		xml_string = re.sub(r"<p>.*?</p>", remove_extra_spaces, xml_string, flags=re.DOTALL)

	# Remove all newline characters
	xml_string = xml_string.replace("\n", "")

	# Replace <pb type="orig"/></p> with </p><pb type="orig"/>
	xml_string = xml_string.replace('<pb type="orig"/></p>', '</p><pb type="orig"/>')

	# Remove <lb> tags before </p> and before the first <p>
	xml_string = xml_string.replace("<lb/></p>", "</p>")
	xml_string = xml_string.replace('<lb break="line"/></p>', "</p>")
	xml_string = xml_string.replace('<p><lb break="line"/>', "<p>", 1)

	# Insert newline characters before block-level tags
	xml_string = insert_newlines_before_block_tags(xml_string)

	# Put <pb/> tags on separate lines
	pattern = r"(<pb [^>]*?/>)"
	xml_string = re.sub(pattern, r"\n\1\n", xml_string)

	# Insert newlines before <lb/>
	pattern = r"(<lb[^/]*?/>)"
	xml_string = re.sub(pattern, r"\n\1", xml_string)

	# Remove closing and opening paragraph tags if there is an <lb>
 	# tag indicating hyphenated word in the line break
	xml_string = xml_string.replace('\n<lb break="word"/>\n</p>\n<p>', '\n<lb break="word"/>')

	# Add space before ... if preceeded by a word character
	# remove space between full stops and standardize two full stops to three
	pattern = re.compile(r"(\w) *\. *\.( *\.)?")
	xml_string = pattern.sub(r"\1 ...", xml_string)

	if NORMALIZE_LARGE_NUMBERS:
		# For numbers over 999 that have normal space or comma as separator:
		# replace those separators with the normalized separator.
		xml_string = normalize_and_format_numbers(
			xml_string,
			NORMALIZED_THOUSAND_SEPARATOR,
			REG_ENCODE_NUMBERS_NORMALIZATION
		)

		# Add thousand separator in numbers over 999 without separator.
		# Numbers between EXCLUDE_NUMBERS_NORM_MIN and 
		# EXCLUDE_NUMBERS_NORM_MAX are most likely years and shouldn't
		# contain any space, so leave them out of the replacement.
		xml_string = add_thousand_separators(
			xml_string,
			NORMALIZED_THOUSAND_SEPARATOR,
			REG_ENCODE_NUMBERS_NORMALIZATION,
			EXCLUDE_NUMBERS_NORM_MIN,
			EXCLUDE_NUMBERS_NORM_MAX
		)

	# The asterisk stands for a footnote
	pattern = re.compile(r" *\*\) *")
	xml_string = pattern.sub("<note xml:id=\"ftn\" n=\"*)\" place=\"foot\"></note>", xml_string)

	# Replace certain characters
	pattern = re.compile(r"&quot;")
	xml_string = pattern.sub("”", xml_string)
	pattern = re.compile(r"&apos;")
	xml_string = pattern.sub("’", xml_string)
	pattern = re.compile(r"º")
	xml_string = pattern.sub("<hi rend=\"raised\">o</hi>", xml_string)

	# There should be a non-breaking space before %
	pattern = re.compile(r"([^  ])%")
	xml_string = pattern.sub(r"\1&#x00A0;%", xml_string)
	pattern = re.compile(r" %")
	xml_string = pattern.sub(r"&#x00A0;%", xml_string)

	# Content of element note shouldn't start with space
	pattern = re.compile(r"(<note .+?>) ")
	xml_string = pattern.sub(r"\1", xml_string)

	# Replace any " characters in text nodes with typographic
	# right double quotation mark ” as " may only occur inside tags
	# for attribute values. This method first temporarily replaces
	# all " with ” and then reverts ” back to " inside tags.
	xml_string = xml_string.replace('"', '”')
	xml_string = re.sub(r'<[^>]+>', doublequotes_to_straightquotes, xml_string)

	# Remove multiple consecutive space characters
	pattern = re.compile(r" +")
	xml_string = pattern.sub(" ", xml_string)

	# Standardize certain other characters
	xml_string = xml_string.replace("„", "”")
	xml_string = xml_string.replace("‟", "”")
	xml_string = xml_string.replace("“", "”")
	xml_string = xml_string.replace("»", "”")
	xml_string = xml_string.replace("«", "”")
	xml_string = xml_string.replace("—", "–")
	xml_string = xml_string.replace("\'", "’")
	xml_string = xml_string.replace("’’", "”")
	xml_string = xml_string.replace("´", "’")

	# Indent lines starting with <lb/> within <p>
	xml_string = re.sub(r"<p>.*?</p>", indent_lb_tags, xml_string, flags=re.DOTALL)

	# Indent lines starting with <l> within <lg>
	xml_string = re.sub(r"<lg>.*?</lg>", indent_l_tags, xml_string, flags=re.DOTALL)

	# Indent <item> elements
	xml_string = xml_string.replace("<item>", "\t<item>")

	if PRESERVE_LB_TAGS:
		# Change <lb/> break type to word if previous line ends with hyphen
		# marked by <pc> tag.
		xml_string = xml_string.replace('<pc>-</pc>\n\t<lb break="line"/>', '<pc>-</pc>\n\t<lb break="word"/>')
	else:
		# Remove whitespace characters at the start or end of paragraph tags
		pattern = re.compile(r"<p>\s*")
		xml_string = pattern.sub("<p>", xml_string)
		pattern = re.compile(r"\s*</p>")
		xml_string = pattern.sub("</p>", xml_string)
		# Remove space character after closing <pc> tag
		xml_string = xml_string.replace("</pc> ", "</pc>")

	# Remove empty <p/>
	xml_string = xml_string.replace("<p>\n</p>", "<p/>")
	xml_string = xml_string.replace("<p/>\n", "")
	xml_string = xml_string.replace("<p/>", "")
	xml_string = xml_string.replace("<p></p>", "")

	# Replace multiple consecutive newlines with a single newline
	xml_string = re.sub(r"\n+", "\n", xml_string)

	# Ensure line break before <p>
	xml_string = xml_string.replace("</p><p>", "</p>\n<p>")

	if CHECK_UNTAGGED_ABBREVIATIONS is True:
		xml_string = replace_untagged_abbreviations(xml_string, abbr_dictionary)

	return xml_string


def insert_newlines_before_block_tags(text: str) -> str:
	before_tags = [
		"<root>", "</root>", "<div>", "</div>", "<p>", "</p>", "<lg>", "</lg>",
		"<list>", "</list>", "<quote>", "</quote>",
		"<head>", "<item>", "<l>"
	]

	for tag in before_tags:
		text = text.replace(tag, "\n" + tag)

	tags_with_attr = [
		"div", "p", "lg", "head", "l", "list", "quote"
	]

	# Loop through each tag in the list
	for name in tags_with_attr:
		# Create the regex pattern dynamically
		pattern = fr"(<{name} [^>]+?>)"
		# Perform the replacement
		text = re.sub(pattern, r"\n\1", text)

	return text


# Function to remove newlines within a match
def newlines_to_spaces(match):
	return match.group(0).replace("\n", " ")


# Function to replace multiple consecutive whitespace characters within a 
# match with a single space
def remove_extra_spaces(match):
	# Replace all sequences of whitespace characters with a single space
	return re.sub(r"\s+", " ", match.group(0))


def remove_hyphenated_newlines(match):
	return match.group(0).replace("-<lb/>", "")


def indent_lb_tags(match):
	return re.sub(r"\n(<lb [^>]*?/>)", r"\n\t\1", match.group(0))


def indent_l_tags(match):
	return match.group(0).replace("\n<l>", "\n\t<l>")


def doublequotes_to_straightquotes(match):
	return match.group(0).replace('”', '"')


# if abbreviations haven't been encoded but we still want to
# add likely expansions to them: use this option
def replace_untagged_abbreviations(xml_string, abbr_dictionary):
	# certain words should only be given expans if they have
	# been encoded as abbrs, otherwise they probably aren't
	# abbrs but just ordinary words that can't be expanded
	# keep these words in this list
	do_not_expand = ["a.", "adress.", "af", "af.", "afsigt", "allmän", "angelägen", "angelägen.", "art", "B", "B.", "beslut", "beslut.", "bl.", "borg", "borg.", "c.", "d", "D", "D.", "dat", "del", "del.", "des", "E", "E.", "erkände", "f.", "f:", "F.", "fl.", "fr", "Fr", "Fr.", "följ", "Följ", "för", "för.", "föredrag", "förhand", "förhand.", "förord", "först", "först.", "G.", "ge", "ge.", "gen", "gifter", "gång.", "H", "H.", "hand.", "just", "Just", "k.", "K", "K.", "K. F", "K. F.", "kg", "kung", "Kung", "l", "L", "L.", "lämpligt", "lämpligt.", "m", "m.", "M", "M.", "Maj.", "med", "med.", "min", "min.", "mån", "n", "n.", "N", "N.", "nu", "nu.", "ord", "ord.", "period", "period.", "propos", "public", "R", "R.", "redo", "regn", "regn.", "rest", "rest.", "rörde", "s", "s.", "S", "S.", "sammans.", "säg", "Säg", "sigill", "St", "St.", "S<hi rend=\"raised\">t", "S<hi rend=\"raised\">t</hi> Petersburg", "system.", "t.", "tills", "Tills", "tur", "upp", "upp.", "utfärd", "utfärd.", "v.", "verk.", "väg.", "W", "W.", "öfver."]
	# these are all the recorded abbrs that we hav en expan for
	abbr_list = abbr_dictionary.keys()
	for abbreviation in abbr_list:
		if abbreviation in do_not_expand:
			continue
		# prevent abbrs containing a dot from being treated as regex
		# otherwise e.g. abbr "Fr." matches "Fri" in the text
		abbreviation_in_text = re.escape(abbreviation)
		# by adding some context to the abbr we can specify 
		# what a word should look like and make sure that parts
		# of words or already tagged words don't get tagged 
		pattern = re.compile(r"(\s|^|»|”|\()" + abbreviation_in_text + r"(\s|\.|,|\?|!|»|”|:|;|\)|<lb/>|</p>)", re.MULTILINE)
		result = pattern.search(xml_string)

		if result is not None:
			# get the expan for this abbr and substitute this
			# part of the text
			expansion = abbr_dictionary[abbreviation]
			xml_string = pattern.sub(r"\1" + "<choice><abbr>" + abbreviation + "</abbr><expan>" + expansion + "</expan></choice>" r"\2", xml_string)

	return xml_string


def add_thousand_separators(text, separator, reg_encode, exclude_min, exclude_max):
	# Function to format the number with narrow non-breaking space as a separator
	def format_number(match):
		# Extract the number from the match object
		number = match.group()
		number_int = int(number)

		# If the number is not in the exclude range or there is no exclude range,
		# proceed with adding separators.
		if (exclude_min < 0 and exclude_max < 0) or number_int < exclude_min or number_int > exclude_max:
			# Split the number into groups of three from the end
			parts = []
			while number:
				parts.append(number[-3:])
				number = number[:-3]
			# Reverse the parts (since we've built them from the end) and join them
			formatted_number = separator.join(reversed(parts))
			if reg_encode:
				return f"<reg>{formatted_number}</reg>"
			else:
				return formatted_number
		else:
			return number

	# Replace all occurrences of numbers with four or more digits in the text
	return re.sub(r'\b\d{4,}\b', format_number, text)


def normalize_and_format_numbers(text, new_separator, reg_encode):
	# Remove existing thousand separators (spaces and commas) and reinsert uniformly
	def reformat_with_separator(match):
		# Remove all non-digit characters to handle numbers with mixed or incorrect current formatting
		cleaned_number = re.sub(r'[,\s]', '', match.group())
		# Convert to integer to remove leading zeros if any
		number = int(cleaned_number)
		# Reformat with the new separator
		formatted_number = f"{number:,}".replace(",", new_separator)
		if reg_encode:
			return f"<reg>{formatted_number}</reg>"
		else:
			return formatted_number

	# Regex to find numbers with potential separators: includes comma or space separated.
	# \d{1,3} matches up to three digits (covering cases like 1,000 to 999,999), and
 	# (?:[,\s]\d{3})+ matches groups of three digits prefixed by either a comma or a space
	# one or more times.
	return re.sub(r'\b\d{1,3}(?:[,\s]\d{3})+\b', reformat_with_separator, text)


def combine_quote_blocks(soup):
	"""
	Combines consecutive sibling <quote type="block"> elements in the XML tree.
	
	Parameters:
			soup (BeautifulSoup): A BeautifulSoup object representing the parsed XML.
			
	Returns:
			BeautifulSoup: The updated BeautifulSoup object with combined <quote type="block"> elements.
	"""
	# Find all <quote> elements
	all_quotes = soup.find_all("quote")

	# Initialize a variable to track the combined <quote type="block">
	combined_quote = None

	for quote in all_quotes:
			# Check if the current quote is of type="block"
			if quote.get("type") == "block":
					if combined_quote is None:
							# If no combined quote exists, start with this one
							combined_quote = quote
					else:
							# Check if the current <quote> is a sibling of the combined <quote>
							if combined_quote.find_next_sibling() == quote:
									# Append the contents of this quote to the combined quote
									for child in quote.find_all(recursive=False):
											combined_quote.append(child)
									# Remove the current quote
									quote.decompose()
							else:
									# Reset the combined quote if they are not siblings
									combined_quote = quote
			else:
					# Reset the combined quote if a non-matching <quote> is found
					combined_quote = None

	return soup


# save the new xml file in another folder
def write_to_file(tidy_xml_string, filename):
	if not os.path.exists(OUTPUT_FOLDER):
		os.makedirs(OUTPUT_FOLDER)

	if DEBUG:
		newline_char = ""
	else:
		newline_char = None
	output_file = open(os.path.join(OUTPUT_FOLDER, filename), "w", encoding="utf-8", newline=newline_char)
	output_file.write(tidy_xml_string)
	output_file.close()


def print_exe_header():
	header = f"""
################################## TIDY_XML #################################
#
# Version: {SCRIPT_VERSION}
#
# This script is used to transform the formatting of TEI XML documents into
# tidier form. It’s first and foremost tailored for documents exported from 
# Transkribus, but can also be used for documents converted from word 
# processor documents with TEIGarage Conversion.
#
# See the README on https://github.com/slsfi/digital-edition-tidy-xml-py
# for instructions and options.
#
#############################################################################
"""
	print(header)


# Run main script function
if __name__ == "__main__":
	main()
