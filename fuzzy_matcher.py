from rapidfuzz import fuzz
import re

def standardize_weight_to_grams(weight_str):
    """
    Converts various weight strings (70g, 0.07 kg, 70 grams) into a standard float of grams.
    """
    if not weight_str:
        return None
        
    weight_str = str(weight_str).lower().strip()
    
    # Extract the numeric part (e.g. '0.07' from '0.07 Kilograms')
    numeric_match = re.search(r'[\d\.]+', weight_str)
    if not numeric_match:
        return None
        
    value = float(numeric_match.group())
    
    # Check for unit and convert
    if 'kg' in weight_str or 'kilogram' in weight_str:
        return value * 1000.0
    elif 'g' in weight_str or 'gram' in weight_str:
        return value
    else:
        return value

def check_ecommerce_mismatches(physical_data, online_data):
    """
    Compares Physical OCR scan vs E-Commerce API data.
    """
    mismatches = []
    
    # 1. Price Matching (Hard check: if online price > printed MRP, it's a violation)
    physical_mrp = float(physical_data.get('mrp.value', 0))
    online_price = float(online_data.get('online_price', 0))
    
    if online_price > physical_mrp:
        mismatches.append({
            "field": "PRICE",
            "physical": f"Rs. {physical_mrp}",
            "online": f"Rs. {online_price}",
            "issue": "Online seller is charging more than printed MRP!"
        })

    # 2. Weight Matching (Unit conversion check)
    phys_weight_g = standardize_weight_to_grams(physical_data.get('net_quantity.value'))
    onln_weight_g = standardize_weight_to_grams(online_data.get('online_weight'))
    
    if phys_weight_g and onln_weight_g:
        # We allow a tiny 1-gram margin of error for floating point math
        if abs(phys_weight_g - onln_weight_g) > 1.0: 
            mismatches.append({
                "field": "WEIGHT",
                "physical": physical_data.get('net_quantity.value'),
                "online": online_data.get('online_weight'),
                "issue": "Physical weight does not match listed online weight!"
            })

    # 3. Manufacturer Matching (Fuzzy string check)
    phys_mfg = str(physical_data.get('manufacturer.name', ''))
    onln_mfg = str(online_data.get('online_manufacturer', ''))
    
    # RapidFuzz returns a score from 0 to 100. 
    # Let's say anything below 80 is a mismatch.
    similarity_score = fuzz.token_sort_ratio(phys_mfg, onln_mfg)
    
    if similarity_score < 80:
        mismatches.append({
            "field": "MANUFACTURER",
            "physical": phys_mfg,
            "online": onln_mfg,
            "issue": f"Names do not match! (Similarity: {similarity_score:.1f}%)"
        })
        
    return mismatches

if __name__ == "__main__":
    # --- MOCK DATA ---
    physical_scan = {
        "mrp.value": "14.00",
        "net_quantity.value": "70g",
        "manufacturer.name": "Nestle India Ltd."
    }
    
    online_listing = {
        "online_price": 25.00,
        "online_weight": "0.07 Kilograms",
        "online_manufacturer": "Nestle India" # Notice this is missing "Ltd."
    }
    
    print("\n[E-COMMERCE CROSS-VERIFICATION ENGINE]")
    print("-" * 50)
    print("Physical Scan:", physical_scan)
    print("Online Data:  ", online_listing)
    print("-" * 50)
    
    results = check_ecommerce_mismatches(physical_scan, online_listing)
    
    if len(results) == 0:
        print("[STATUS: PASS] Online listing perfectly matches physical product.")
    else:
        print(f"[STATUS: WARNING] Found {len(results)} discrepancies!\n")
        for mismatch in results:
            print(f"-> {mismatch['field']} MISMATCH")
            print(f"   Physical: {mismatch['physical']}")
            print(f"   Online:   {mismatch['online']}")
            print(f"   Alert:    {mismatch['issue']}\n")
