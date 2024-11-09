from flask import Flask, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET

# Initialize the Flask application
app = Flask(__name__)

# API Base URLs
PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ELASTICSEARCH_URL = "http://localhost:9200"  # Placeholder URL for future use if Elasticsearch is needed

# Function to search PubMed for papers matching the user's query
def search_pubmed(query):
    # Parameters for PubMed esearch API
    params = {
        'db': 'pubmed',      # Database to search (PubMed)
        'term': query,       # Query term
        'retmode': 'json',   # Return mode in JSON format
        'retmax': 10         # Maximum results to retrieve (top 10)
    }
    # Send a GET request to the PubMed API with the query parameters
    response = requests.get(PUBMED_API_BASE, params=params)
    data = response.json()  # Parse response as JSON
    
    # Return the list of PubMed paper IDs from the search results
    return data['esearchresult']['idlist']

# Function to fetch detailed information for a list of PubMed paper IDs
def get_pubmed_details(paper_ids):
    # Base URL for the PubMed efetch API
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    ids = ",".join(paper_ids)  # Convert list of paper IDs to a comma-separated string
    
    # Parameters for the efetch request
    params = {
        'db': 'pubmed',      # Database to fetch from (PubMed)
        'id': ids,           # Comma-separated list of paper IDs
        'retmode': 'xml',    # Return mode in XML format
    }
    
    # Send GET request to PubMed API with efetch parameters
    response = requests.get(base_url, params=params)
    data = response.text  # Retrieve raw XML data as a string
    
    return data

# Function to parse the XML response and extract paper titles and abstracts
def parse_pubmed_xml(xml_data):
    # Parse the XML string into an ElementTree object
    root = ET.fromstring(xml_data)
    papers = []  # List to store extracted paper details
    
    # Iterate over each article in the XML data
    for article in root.findall(".//PubmedArticle"):
        title = ""
        abstract = ""
        
        # Extract the article title
        title_element = article.find(".//ArticleTitle")
        if title_element is not None:
            title = title_element.text  # Get the title text if available
        
        # Extract the abstract (can have multiple sections)
        abstract_elements = article.findall(".//AbstractText")
        if abstract_elements:
            # Join multiple abstract sections into one string
            abstract = " ".join([elem.text or "" for elem in abstract_elements])
        
        # Append paper title and abstract to the list of papers
        papers.append({'title': title, 'abstract': abstract})
    
    return papers

# Define the route for the home page, with support for both GET and POST requests
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # If a POST request is made, retrieve the search query from the form
        query = request.form.get("query")
        
        # Search PubMed and get a list of paper IDs
        paper_ids = search_pubmed(query)
        
        # Fetch the details of each paper using the list of IDs
        xml_data = get_pubmed_details(paper_ids)
        # Parse the XML response to get a list of paper titles and abstracts
        papers = parse_pubmed_xml(xml_data)
        
        # Render the results page, passing in the search query and list of papers
        return render_template("results.html", query=query, papers=papers)
    
    # If a GET request is made, render the home page (index.html)
    return render_template("index.html")

# Run the Flask application
if __name__ == "__main__":
    # Run the application on port 8080
    app.run(port=8080)

