from flask import Flask, request, render_template
import torch
import pandas as pd
import re
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Load T5 model and tokenizer
tokenizer = T5Tokenizer.from_pretrained('t5-small')
model = T5ForConditionalGeneration.from_pretrained('t5-small')

class MedicalSearchQuery:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)  # Load the CSV file into a DataFrame
        self.columns = ["Gender", "Symptoms", "Occupation"]  # Columns to be used in the query
        self.unique_terms = self.extract_unique_terms()  # Extract unique terms for each column

    def extract_unique_terms(self):
        unique_terms = {}
        for col in self.columns:
            if col in self.df.columns:
                # Normalize terms by splitting and removing whitespace variations
                terms = self.df[col].dropna().str.lower().str.split(',').explode().str.strip()
                normalized_terms = set()
                for term in terms:
                    # Add variations of each term (e.g., with/without spaces or hyphens)
                    normalized_terms.add(term)
                    normalized_terms.add(term.replace(" ", ""))
                    normalized_terms.add(term.replace(" ", "-"))
                unique_terms[col] = normalized_terms
        return unique_terms

    def preprocess_with_t5(self, input_text):
        # Preprocess input text using T5 for summarization
        input_ids = tokenizer("summarize: " + input_text, return_tensors="pt").input_ids
        output_ids = model.generate(input_ids, max_length=50, num_beams=4, early_stopping=True)
        summarized_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return summarized_text

    def parse_input(self, input_text):
        parsed_terms = {col: [] for col in self.columns}
        negations = []
        input_text = input_text.lower()

        # Split text on 'without' to identify negations in the query
        parts = re.split(r"\bwithout\b", input_text)
        positive_text = parts[0].strip() if parts else input_text  # Positive terms before "without"
        negative_text = parts[1].strip() if len(parts) > 1 else ""  # Negative terms after "without"

        # Match positive terms from unique_terms against input text
        for col, terms in self.unique_terms.items():
            for term in terms:
                pattern = rf"\b{term}\b"
                if re.search(pattern, positive_text, re.IGNORECASE):
                    parsed_terms[col].append(term.replace("-", " "))  # Add matched term to parsed_terms

        # Match negations from unique_terms against text following 'without'
        for col, terms in self.unique_terms.items():
            for term in terms:
                pattern = rf"\b{term}\b"
                if re.search(pattern, negative_text, re.IGNORECASE):
                    negations.append(term.replace("-", " "))  # Add matched term to negations list

        # Remove any empty entries in parsed_terms
        parsed_terms = {k: v for k, v in parsed_terms.items() if v}
        return parsed_terms, negations

    def generate_boolean_query(self, parsed_terms, negations):
        if not parsed_terms:
            return "No matching terms found in the input."

        query_parts = []
        # Format parsed terms for Boolean OR conditions
        for _, terms in parsed_terms.items():
            formatted_terms = " OR ".join([f'"{term}"' for term in terms])
            query_parts.append(f"({formatted_terms})")

        # Format negations with NOT condition
        if negations:
            negation_terms = " OR ".join([f'"{negation}"' for negation in negations])
            query_parts.append(f"NOT ({negation_terms})")

        final_query = " AND ".join(query_parts)
        return final_query

    def get_boolean_query(self, input_text):
        summarized_text = self.preprocess_with_t5(input_text)  # Summarize input using T5
        parsed_terms, negations = self.parse_input(summarized_text)  # Parse summarized input
        boolean_query = self.generate_boolean_query(parsed_terms, negations)  # Generate Boolean query
        return boolean_query, parsed_terms, negations

    def filter_data(self, parsed_terms, negations):
        filtered_df = self.df.copy()  # Create a copy of the DataFrame for filtering

        # Filter DataFrame by parsed terms in relevant columns
        for col, terms in parsed_terms.items():
            if col in filtered_df.columns:
                condition = filtered_df[col].str.contains("|".join(terms), case=False, na=False)
                filtered_df = filtered_df[condition]

        # Exclude rows that contain negations in the specified column
        for negation in negations:
            if "Occupation" in filtered_df.columns:  # Adjust if negation applies to different columns
                filtered_df = filtered_df[~filtered_df["Occupation"].str.contains(negation, case=False, na=False)]

        return filtered_df

# Flask App Initialization
app = Flask(__name__)

# CSV file path
file_path = "C:/Users/Intel/Documents/med/meddataa.csv"
search_query = MedicalSearchQuery(file_path)

# Define the routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_query', methods=['POST'])
def generate_query():
    user_input = request.form['query']
    boolean_query, parsed_terms, negations = search_query.get_boolean_query(user_input)  # Generate query
    matching_records = search_query.filter_data(parsed_terms, negations)  # Filter records by query terms
    return render_template('index.html', input=user_input, output=boolean_query, records=matching_records.to_dict(orient='records'))

if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode

