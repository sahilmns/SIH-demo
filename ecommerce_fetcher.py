import requests
import json

def fetch_amazon_listing(url, api_key=None):
    """
    Fetches product details from Amazon using a generic Product API (like Rainforest API).
    If no API key is provided, it returns a mock JSON response so you can test immediately.
    """
    if not api_key:
        print("[WARNING] No API key provided. Returning Mock JSON Data for testing...")
        return get_mock_api_response()
        
    # This is how the real API call will look once you sign up for one
    api_endpoint = "https://api.rainforestapi.com/request"
    params = {
        "api_key": api_key,
        "type": "product",
        "amazon_domain": "amazon.in",
        "url": url
    }
    
    try:
        response = requests.get(api_endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_mock_api_response():
    """Simulates the massive JSON payload that e-commerce APIs return."""
    return {
        "request_info": {"success": True},
        "product": {
            "title": "Maggi 2-Minute Instant Noodles, 70g",
            "brand": "Maggi",
            "buybox_winner": {
                "price": {
                    "value": 25.00, # Intentionally higher than our 14.00 physical scan!
                    "currency": "INR"
                }
            },
            "specifications": [
                {"name": "Weight", "value": "0.07 Kilograms"}, # Online uses kg instead of g
                {"name": "Manufacturer", "value": "Nestle India Ltd"},
                {"name": "Country of Origin", "value": "India"}
            ]
        }
    }

def extract_relevant_fields(api_json):
    """
    Parses the massive API JSON response into just the fields we need 
    to compare against our Physical Product OCR scan.
    """
    if not api_json or 'product' not in api_json:
        return None
        
    product = api_json['product']
    
    # Safely extract price
    price = None
    if 'buybox_winner' in product and 'price' in product['buybox_winner']:
        price = product['buybox_winner']['price']['value']
        
    # Safely extract specs from the table on the Amazon page
    weight = None
    manufacturer = None
    if 'specifications' in product:
        for spec in product['specifications']:
            if 'weight' in spec['name'].lower():
                weight = spec['value']
            elif 'manufacturer' in spec['name'].lower():
                manufacturer = spec['value']
                
    return {
        "online_title": product.get('title'),
        "online_brand": product.get('brand'),
        "online_price": price,
        "online_weight": weight,
        "online_manufacturer": manufacturer
    }

if __name__ == "__main__":
    print("\n--- INITIATING E-COMMERCE FETCH ---")
    test_url = "https://www.amazon.in/Maggi-2-Minute-Instant-Noodles-70g/dp/B00123456"
    print(f"Target URL: {test_url}\n")
    
    # In the future, you will run: fetch_amazon_listing(test_url, api_key="YOUR_REAL_KEY")
    raw_api_data = fetch_amazon_listing(test_url)
    
    print("\n--- RAW API JSON (SIMULATED) ---")
    # Print the raw data to show the format
    print(json.dumps(raw_api_data, indent=2))
    
    print("\n--- CLEANED DATA FOR MATCHING ENGINE ---")
    clean_data = extract_relevant_fields(raw_api_data)
    print(json.dumps(clean_data, indent=2))
    print("\nNotice how the API returns '0.07 Kilograms' and '25.00 INR'.")
    print("Next step: Build the fuzzy matcher to compare this to our physical '70g' and '14.00 INR'!")
