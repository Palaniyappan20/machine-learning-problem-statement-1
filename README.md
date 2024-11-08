Medical Search Query Generator

A web-based application to generate Boolean search queries from user-provided medical terms and return matching records from a CSV dataset. Built with Flask, this application allows users to enter a natural language search query, which is then processed to generate a structured Boolean query. The application then displays matching data records based on the generated Boolean query.

Features

- Generates a Boolean query based on user input.
- Parses natural language input for medical symptoms, gender, and occupation.
- Searches a medical dataset for matching records and displays them on a web page.
- User-friendly interface for non-technical users.

Technologies Used

- Python
- Flask
- Pandas (for data manipulation)
- HTML (for web form and table display)

Getting Started

Prerequisites

- Python 3.x
- Flask and Pandas libraries

To install Flask and Pandas, run:

pip install Flask pandas

Project Structure:

Medical-Search-Query-Generator/
│
├── app.py                 
├── meddata.csv           
└── templates/
    └── index.html   
