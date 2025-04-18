import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio

# --- Web Scraping Function (remains the same) ---
def scrape_medical_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        data = []
        tables = soup.find_all('table')
        if tables:
            table = tables[0]
            headers = [th.text.strip() for th in table.find_all('th')]
            for tr in table.find_all('tr')[1:]:
                row_data = [td.text.strip() for td in tr.find_all('td')]
                if len(headers) == len(row_data):
                    data.append(dict(zip(headers, row_data)))
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Request failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during scraping: {e}")

# --- Pydantic Model for Request Body (Optional but Recommended) ---
class ScrapingRequest(BaseModel):
    url: str

# --- FastAPI Application ---
app = FastAPI()

@app.post("/scrape")
async def scrape_data_endpoint(request: ScrapingRequest):
    """
    Scrape medical data from the provided URL and return it as JSON.
    """
    data = scrape_medical_data(request.url)
    return JSONResponse(content=data)

# --- Streamlit Integration ---
def main():
    st.title("Medical Data API (Powered by FastAPI)")
    st.write("Interact with the API endpoint to scrape medical data.")

    st.subheader("Test the /scrape endpoint:")
    url_input = st.text_input("Enter URL to scrape:")
    if st.button("Send Scraping Request"):
        if url_input:
            try:
                response = requests.post("http://localhost:8000/scrape", json={"url": url_input})
                response.raise_for_status()
                scraped_data = response.json()
                st.subheader("Scraped Data (from API):")
                st.json(scraped_data)
            except requests.exceptions.RequestException as e:
                st.error(f"Error calling API: {e}")
            except json.JSONDecodeError:
                st.error("Received invalid JSON response from the API.")
        else:
            st.warning("Please enter a URL.")

if __name__ == "__main__":
    # Run FastAPI in the background using asyncio
    async def run_fastapi():
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.create_task(run_fastapi())

    # Run the Streamlit app
    main()
