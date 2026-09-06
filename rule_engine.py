import json

def evaluate_logic(mock_data, logic):
    field = logic['field']
    operator = logic['operator']
    expected = logic['expected_value']
    
    # Get the value extracted by our mock OCR
    actual_value = mock_data.get(field, None)
    
    # Handle different types of logic rules
    if operator == 'EXISTS':
        # Condition passes if the value exists and is not empty
        return bool(actual_value)
    
    elif operator == 'NOT_EXISTS':
        return not bool(actual_value)
        
    elif operator in ['EQUALS', '==', '=']:
        return str(actual_value).strip().lower() == str(expected).strip().lower()
        
    elif operator == 'CONTAINS':
        if not actual_value: return False
        return str(expected).strip().lower() in str(actual_value).strip().lower()
        
    elif operator == 'NOT_ALTERED':
        # For things like MRP smudging. If the OCR detects alteration = True, this fails.
        return actual_value == False
        
    # If the operator is complex or not yet implemented in our prototype, we assume False
    # so that the team knows they need to implement it!
    return False

def run_compliance_check(product_data, rules_file='METRA_X_Rule_Engine.json'):
    with open(rules_file, 'r', encoding='utf-8') as f:
        rules = json.load(f)
        
    report = {
        "status": "PASS",
        "violations": []
    }
    
    for rule in rules:
        rule_id = rule['rule_id']
        
        for logic in rule['logics']:
            # Skip logics that are N/A or empty
            if not logic['field'] or logic['field'] == 'N/A': continue
                
            passed = evaluate_logic(product_data, logic)
            
            if not passed:
                report["status"] = "FAIL"
                report["violations"].append({
                    "rule_id": rule_id,
                    "logic_id": logic['logic_id'],
                    "category": rule['category'],
                    "violation_type": rule['violation_type'],
                    "message": logic['violation_message'],
                    "evidence": f"Field '{logic['field']}' failed the '{logic['operator']}' check. OCR extracted value: '{product_data.get(logic['field'], 'Missing/Null')}'"
                })
                
    return report

if __name__ == "__main__":
    # ==========================================
    # MOCK OCR DATA (The "Contract")
    # This is what your OCR team must eventually output.
    # We are simulating a product where the Address and Email are missing,
    # and the MRP has been altered/smudged.
    # ==========================================
    mock_ocr_data = {
        "package.declaration_set": True,
        "manufacturer.name": "Nestle India Ltd.",
        "manufacturer.address": "", # Intentionally missing to trigger violation
        "product.common_or_generic_name": "Maggi Noodles",
        "net_quantity.value": "70g",
        "mrp.value": "14.00",
        "manufacture_or_pack_or_import_date": "10/2025",
        "consumer_contact.telephone": "1800-103-1947",
        "consumer_contact.email": "", # Intentionally missing
        "mrp.altered_by_trade_party": True # Intentionally set to True to flag violation
    }
    
    print("\n" + "="*50)
    print("[METRA-X RULE ENGINE PROTOTYPE]")
    print("="*50)
    print("Mock OCR Data Received:")
    print(json.dumps(mock_ocr_data, indent=2))
    print("-" * 50)
    
    # Run the engine!
    results = run_compliance_check(mock_ocr_data)
    
    # Print the report
    if results['status'] == 'PASS':
        print("\n[STATUS: COMPLIANT]")
        print("All packaged commodity rules passed successfully.")
    else:
        print(f"\n[STATUS: FAIL] - Found {len(results['violations'])} Violations\n")
        for idx, v in enumerate(results['violations'], 1):
            print(f"[{idx}] Rule {v['rule_id']} ({v['category']})")
            print(f"    Violation: {v['violation_type']}")
            print(f"    Message:   {v['message']}")
            print(f"    Evidence:  {v['evidence']}\n")
