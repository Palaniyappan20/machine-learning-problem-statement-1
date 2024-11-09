from flask import Flask, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

# API Base URLs
PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ELASTICSEARCH_URL = "http://localhost:9200"  # Assuming you want to use this later

# Fetch papers from PubMed using the Entrez API (esearch)
def search_pubmed(query):
    params = {
        'db': 'pubmed',
        'term': query,
        'retmode': 'json',
        'retmax': 10  # Retrieve only the top 10 results
    }
    response = requests.get(PUBMED_API_BASE, params=params)
    data = response.json()
    
    # Return list of PubMed paper IDs
    return data['esearchresult']['idlist']

# Fetch full paper details from PubMed using efetch
def get_pubmed_details(paper_ids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    ids = ",".join(paper_ids)
    
    params = {
        'db': 'pubmed',
        'id': ids,
        'retmode': 'xml',
    }
    
    response = requests.get(base_url, params=params)
    data = response.text  # Raw XML response
    
    return data

# Parse the XML to extract paper titles and abstracts
def parse_pubmed_xml(xml_data):
    root = ET.fromstring(xml_data)
    papers = []
    
    for article in root.findall(".//PubmedArticle"):
        title = ""
        abstract = ""
        
        # Extract title
        title_element = article.find(".//ArticleTitle")
        if title_element is not None:
            title = title_element.text
        
        # Extract abstract
        abstract_elements = article.findall(".//AbstractText")
        if abstract_elements:
            abstract = " ".join([elem.text or "" for elem in abstract_elements])
        
        papers.append({'title': title, 'abstract': abstract})
    
    return papers

# Define routes
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query")
        
        # Get paper IDs
        paper_ids = search_pubmed(query)
        
        # Fetch and parse details of the papers
        xml_data = get_pubmed_details(paper_ids)
        papers = parse_pubmed_xml(xml_data)
        
        return render_template("results.html", query=query, papers=papers)
    return render_template("index.html")

# Run the Flask application
if __name__ == "__main__":
    app.run(port=8080)
