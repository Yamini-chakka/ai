import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv
import random
import ollama  # LLaMA via Ollama
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")
CHUNK_SIZE = 300  # smaller chunks = faster
TOP_K = 1  # faster similarity search
OLLAMA_MODEL = "llama3"  # Ensure this model is pulled: ollama pull llama3

# ----------------- Utility Functions -----------------

def read_excel(file_path):
    return pd.read_excel(file_path)

def scrape_website(url):
    try:
        print(f"[INFO] Scraping: {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        texts = [tag.get_text(strip=True) for tag in soup.find_all(["p", "h1", "h2", "h3", "li", "span"])]
        return "\n".join(texts)
    except Exception as e:
        print(f"[ERROR] Failed to scrape {url}: {e}")
        return ""

def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def embed_and_store(company, url, chunks):
    for chunk in chunks:
        embedding = model.encode(chunk).tolist()
        response = supabase.table("company_embeddings").insert({
            "company_name": company,
            "url": url,
            "content": chunk,
            "embedding": embedding
        }).execute()
        if hasattr(response, "status_code") and response.status_code != 201:
            print(f"[ERROR] Failed to insert into Supabase: {response}")

def similarity_search(query, company):
    query_vec = model.encode(query).tolist()
    response = supabase.rpc("match_embeddings", {
        "query_embedding": query_vec,
        "match_count": TOP_K,
        "company_name": company
    }).execute()

    if response.data:
        return [item["content"] for item in response.data]
    else:
        print(f"[WARN] No match found for: {query}")
        return []

def ask_llama(prompt):
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{
            "role": "user",
            "content": prompt
        }])
        return response['message']['content'].strip()
    except Exception as e:
        return f"LLaMA Error: {e}"

# ----------------- Prompt Generation ----------------

def get_prompt(company, col, context):
    return f"""
You are given web content related to the company '{company}'.
Using the context below, provide a **single word or very short phrase (maximum 3 words)** that best answers the column titled: '{col}'. 

Context:
{context}

Answer (1 to 3 words only, no explanations):
"""

# ----------------- Main Processing -----------------

def process_companies(df):
    for idx, row in df.iterrows():
        company = row['Company Name']
        url = row['Company URL']
        print(f"\n Processing company: {company}")
        full_text = scrape_website(url)
        if not full_text:
            continue
        chunks = chunk_text(full_text)
        embed_and_store(company, url, chunks)
        time.sleep(1)  # Be nice to servers

def process_row(idx, row, columns_to_fill):
    company = row["Company Name"]
    print(f"\n Generating info for: {company}")
    updated_row = row.copy()
    context_cache = {}

    for col in columns_to_fill:
        if pd.notna(row[col]):
            continue

        if col not in context_cache:
            similar_chunks = similarity_search(col, company)
            context_cache[col] = "\n".join(similar_chunks)

        prompt = get_prompt(company, col, context_cache[col])
        result = ask_llama(prompt)

        updated_row[col] = result
        print(f"[{company} - {col}] => {result}")
        time.sleep(random.uniform(0.1, 0.3))  # faster
    return idx, updated_row

def fill_columns(df):
    columns_to_fill = [col for col in df.columns if col not in ['Company Name', 'Company URL']]

    for col in columns_to_fill:
        df[col] = df[col].astype('object')

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_row, idx, row, columns_to_fill) for idx, row in df.iterrows()]
        for future in as_completed(futures):
            idx, updated_row = future.result()
            df.loc[idx] = updated_row

    return df

# ----------------- Main -----------------

if __name__ == "__main__":
    start_time = time.time()
    df = read_excel("Book1.xlsx")
    process_companies(df)     # Step 1: Scrape and embed
    df = fill_columns(df)     # Step 2: Fill using LLaMA
    df.to_excel("data.xlsx", index=False)
    print(f"\n All company info enriched and saved. Total time: {time.time() - start_time:.2f} seconds")
