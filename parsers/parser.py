import pandas as pd
import json
import sqlite3
import PyPDF2

def parse_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_dict(orient='records')

def parse_excel(file_path):
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')

def parse_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {"raw_text": content}

def parse_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return {"parsed_text": text}

def parse_sqlite(db_path, query="SELECT * FROM main_table"):
    # This is an example, could be more dynamic
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')

def parse_file(file_path, file_type):
    if file_type.lower() == 'csv':
        return parse_csv(file_path)
    elif file_type.lower() in ['xls', 'xlsx']:
        return parse_excel(file_path)
    elif file_type.lower() == 'json':
        return parse_json(file_path)
    elif file_type.lower() == 'txt':
        return parse_txt(file_path)
    elif file_type.lower() == 'pdf':
        return parse_pdf(file_path)
    elif file_type.lower() == 'sqlite':
        return parse_sqlite(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_type}")
