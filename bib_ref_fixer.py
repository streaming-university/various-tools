import re
import glob
import requests
import argparse


def test_url_for_404(x):
    """Test a url for 404"""
    try:
        response = requests.get(x, timeout=5)
        return response.status_code == 404
    except Exception:
        return True


def find_urls_regex(text):
    """Find all urls in a text using a regex"""
    # Regex to find urls
    url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    # Find all urls in the text
    urls = re.findall(url_regex, text)

    return [x[0] for x in urls]


def find_all_refs_in_bib(text, just_keys=True):
    dictionary = {}

    at_flag = False
    comma_flag = False
    open_count = 0
    close_count = 0
    ref = ""
    name = ""

    for char in text:
        if char == "@":
            at_flag = True

        if at_flag:
            ref += char

        if at_flag and open_count == 1 and close_count == 0 and not comma_flag:
            if char == ",":
                comma_flag = True
            else:
                name += char

        if char == "{":
            open_count += 1
        if char == "}":
            close_count += 1
        if open_count == close_count and open_count != 0:
            at_flag = False
            open_count = 0
            close_count = 0
            comma_flag = False
            dictionary[name] = ref
            ref = ""
            name = ""

    if just_keys:
        return list(dictionary.keys())
    else:
        return dictionary


def find_all_citations(text):
    """Find all citations in a tex file"""
    # Regex to find citations
    citation_regex = r"\\cite\{.*?\}"

    # Find all citations in the text
    citations = re.findall(citation_regex, text)

    citations = [citation.split("{")[1].split("}")[0] for citation in citations]

    # Split the citations if there are multiple citations in one command
    citations = [citation.split(",") for citation in citations]

    # Flatten the list
    citations = [item for sublist in citations for item in sublist]

    return citations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    args = parser.parse_args()

    # Find all tex files in the input directory
    tex_files = glob.glob(args.input + "/**/*.tex", recursive=True)

    # Print the number of tex files found
    print("Found {} tex files".format(len(tex_files)))

    # Find all bib files in the input directory
    bib_files = glob.glob(args.input + "/**/*.bib", recursive=True)

    # Print the number of bib files found
    print("Found {} bib files".format(len(bib_files)))

    # Find all urls in the tex files
    tex_urls = set()
    for tex_file in (tex_files + bib_files):
        with open(tex_file, "r") as f:
            for url in find_urls_regex(f.read()):
                tex_urls.add(url)

    # Print the number of urls found in the tex files
    print("Found {} urls in tex files".format(len(tex_urls)))

    # Test all urls in the tex files
    print("Testing urls in tex files...")
    for url in tex_urls:
        if test_url_for_404(url):
            print("URL {} is broken".format(url))

    # Find all references in the bib files
    bib_refs = set()
    for bib_file in bib_files:
        with open(bib_file, "r") as f:
            for ref in find_all_refs_in_bib(f.read()):
                bib_refs.add(ref)

    # Print the number of references found in the bib files
    print("Found {} references in bib files".format(len(bib_refs)))

    # Find all citations in the tex files
    tex_citations = set()
    for tex_file in tex_files:
        with open(tex_file, "r") as f:
            for citation in find_all_citations(f.read()):
                tex_citations.add(citation)

    # Print the number of citations found in the tex files
    print("Found {} citations in tex files".format(len(tex_citations)))

    # Find all references that are not cited
    uncited_refs = bib_refs - tex_citations
    print("Found {} uncited references".format(len(uncited_refs)))
    print(uncited_refs) if len(uncited_refs) > 0 else None

    # Save modified bib files
    for bib_file in bib_files:
        with open(bib_file, "r") as f:
            bib_text = f.read()
            refs = find_all_refs_in_bib(bib_text, just_keys=False)

            # Filter out uncited references
            refs = {k: v for k, v in refs.items() if k not in uncited_refs}

        with open(bib_file, "w") as f:
            f.write("\n\n".join(refs.values()))

    # Done
    print("Done")