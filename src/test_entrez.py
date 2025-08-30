import requests
import xml.etree.ElementTree as ET

pmcid = "PMC5334499"

# 1. Convert PMCID -> PMID
url_conv = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
params = {
    "dbfrom": "pmc",
    "id": pmcid,
    "db": "pubmed",
    "retmode": "xml"
}
r = requests.get(url_conv, params=params)
root = ET.fromstring(r.text)

pmid = None
for elem in root.findall(".//LinkSetDb/Link/Id"):
    pmid = elem.text
    break

if not pmid:
    raise ValueError(f"No PMID found for {pmcid}")

print("PMID:", pmid)

# 2. Fetch abstract using PMID
url_fetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
params = {
    "db": "pubmed",
    "id": pmid,
    "rettype": "abstract",
    "retmode": "xml"
}
r = requests.get(url_fetch, params=params)
root = ET.fromstring(r.text)

abstracts = [abst.text for abst in root.findall(".//AbstractText") if abst.text]
print("Abstract:", " ".join(abstracts))
