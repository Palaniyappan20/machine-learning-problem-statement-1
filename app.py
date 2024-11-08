from flask import Flask, request, render_template
import pandas as pd
import re

class MedicalSearchQuery:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)
        self.columns = ["Gender", "Symptoms", "Occupation"]
        self.unique_terms = self.extract_unique_terms()

    def extract_unique_terms(self):
        unique_terms = {}
        for col in self.columns:
            if col in self.df.columns:
                terms = self.df[col].dropna().str.lower().str.split(',').explode().str.strip()
                normalized_terms = set()
                for term in terms:
                    normalized_terms.add(term)
                    normalized_terms.add(term.replace(" ", ""))
                    normalized_terms.add(term.replace(" ", "-"))
                unique_terms[col] = normalized_terms
        return unique_terms

    def parse_input(self, input_text):
        parsed_terms = {col: [] for col in self.columns}
        input_text = input_text.lower()
        negations = []
        for negation in ["not a student", "not in school", "doesn't study", "non-student"]:
            if negation in input_text:
                negations.append("student")
                input_text = input_text.replace(negation, "")

        for col, terms in self.unique_terms.items():
            for term in terms:
                pattern = rf"\b{term}\b"
                if re.search(pattern, input_text, re.IGNORECASE):
                    parsed_terms[col].append(term.replace("-", " "))
        
        parsed_terms = {k: v for k, v in parsed_terms.items() if v}
        return parsed_terms, negations

    def generate_boolean_query(self, parsed_terms, negations):
        if not parsed_terms:
            return "No matching terms found in the input."
        
        query_parts = []
        for _, terms in parsed_terms.items():
            formatted_terms = " OR ".join([f'"{term}"' for term in terms])
            query_parts.append(f"({formatted_terms})")
        
        if negations:
            negation_terms = " OR ".join([f'"{negation}"' for negation in negations])
            query_parts.append(f"NOT ({negation_terms})")
        
        final_query = " AND ".join(query_parts)
        return final_query

    def get_boolean_query(self, input_text):
        parsed_terms, negations = self.parse_input(input_text)
        boolean_query = self.generate_boolean_query(parsed_terms, negations)
        return boolean_query, parsed_terms, negations

    def filter_data(self, parsed_terms, negations):
        filtered_df = self.df.copy()
        
        for col, terms in parsed_terms.items():
            if col in filtered_df.columns:
                condition = filtered_df[col].str.contains("|".join(terms), case=False, na=False)
                filtered_df = filtered_df[condition]

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
    boolean_query, parsed_terms, negations = search_query.get_boolean_query(user_input)
    matching_records = search_query.filter_data(parsed_terms, negations)
    return render_template('index.html', input=user_input, output=boolean_query, records=matching_records.to_dict(orient='records'))

if __name__ == "__main__":
    app.run(debug=True)
