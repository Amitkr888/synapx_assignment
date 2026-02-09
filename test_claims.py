#!/usr/bin/env python3
"""
Test script for Claims Processing Agent
Processes sample FNOL documents and displays results
"""

import json
from claims_processor import ClaimsProcessor


def process_text_fnol(text_path: str, processor: ClaimsProcessor):
    """
    Process a text-based FNOL document (simulating PDF extraction)
    
    Args:
        text_path: Path to text file
        processor: ClaimsProcessor instance
    """
    import re
    
    with open(text_path, 'r') as f:
        full_text = f.read()
    
    # Simulate the extraction process
    extracted = {
        'policy_information': {},
        'incident_information': {},
        'involved_parties': {},
        'asset_details': {},
        'other_fields': {}
    }
    
    # Extract using the processor's methods
    extracted['policy_information']['policy_number'] = processor._extract_field(
        full_text, r'POLICY NUMBER[:\s]*([A-Z0-9-]+)'
    )
    extracted['policy_information']['policyholder_name'] = processor._extract_field(
        full_text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|INSURED|DATE OF BIRTH)'
    )
    
    extracted['incident_information']['date_of_loss'] = processor._extract_field(
        full_text, r'DATE OF LOSS AND TIME[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    )
    
    time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', full_text, re.IGNORECASE)
    if time_match:
        extracted['incident_information']['time'] = f"{time_match.group(1)} {time_match.group(2)}"
    
    street = processor._extract_field(full_text, r'STREET:[:\s]*([^\n]+)')
    city_state_zip = processor._extract_field(full_text, r'CITY, STATE, ZIP:[:\s]*([^\n]+)')
    
    location_parts = []
    if street and street.strip():
        location_parts.append(street.strip())
    if city_state_zip and city_state_zip.strip():
        location_parts.append(city_state_zip.strip())
    
    extracted['incident_information']['location'] = ', '.join(location_parts) if location_parts else None
    
    extracted['incident_information']['description'] = processor._extract_field(
        full_text, 
        r'DESCRIPTION OF ACCIDENT[:\s]*([^\n]+(?:\n(?!INSURED VEHICLE|DRIVER|OWNER|WITNESSES)[^\n]+)*)'
    )
    
    extracted['involved_parties']['claimant'] = processor._extract_field(
        full_text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|INSURED)'
    )
    
    phone_match = re.search(r'PHONE #[:\s]*PRIMARY[:\s]*(\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4})', full_text)
    if phone_match:
        extracted['involved_parties']['contact_phone'] = phone_match.group(1)
    
    email = processor._extract_field(full_text, r'E-MAIL ADDRESS[:\s]*PRIMARY[:\s]*([^\s\n]+@[^\s\n]+)')
    extracted['involved_parties']['contact_email'] = email
    
    vehicle_year = processor._extract_field(full_text, r'(?:VEH #.*)?YEAR[:\s]*(\d{4})')
    vehicle_make = processor._extract_field(full_text, r'MAKE:[:\s]*([A-Z][A-Za-z]+)')
    vehicle_model = processor._extract_field(full_text, r'MODEL:[:\s]*([A-Za-z0-9\s]+?)(?:\n|BODY)')
    vin = processor._extract_field(full_text, r'V\.I\.N\.:[:\s]*([A-Z0-9]{17})')
    
    extracted['asset_details']['asset_type'] = 'vehicle'
    if vehicle_year or vehicle_make or vehicle_model:
        vehicle_desc = ' '.join(filter(None, [vehicle_year, vehicle_make, vehicle_model]))
        extracted['asset_details']['vehicle_description'] = vehicle_desc
    
    extracted['asset_details']['asset_id'] = vin
    
    estimate = processor._extract_field(full_text, r'ESTIMATE AMOUNT:[:\s]*\$?([0-9,]+(?:\.\d{2})?)')
    if estimate:
        estimate_clean = estimate.replace(',', '')
        try:
            extracted['asset_details']['estimated_damage'] = float(estimate_clean)
        except ValueError:
            extracted['asset_details']['estimated_damage'] = None
    
    claim_type = processor._determine_claim_type(full_text)
    extracted['other_fields']['claim_type'] = claim_type
    
    lob = processor._extract_field(full_text, r'LINE OF BUSINESS[:\s]*([A-Z\s]+?)(?:\n|INSURED)')
    extracted['other_fields']['line_of_business'] = lob
    
    naic = processor._extract_field(full_text, r'CARRIER NAIC CODE[:\s]*(\d+)')
    extracted['other_fields']['naic_code'] = naic
    
    # Process through the pipeline
    flattened = processor.flatten_extracted_data(extracted)
    missing = processor.validate_fields(flattened)
    route, reasoning = processor.route_claim(flattened, missing)
    
    result = {
        "extractedFields": flattened,
        "missingFields": missing,
        "recommendedRoute": route,
        "reasoning": reasoning
    }
    
    return result


def main():
    """Test all sample FNOL documents"""
    
    sample_files = [
        'sample_fnol_1.txt',
        'sample_fnol_2.txt',
        'sample_fnol_3.txt'
    ]
    
    processor = ClaimsProcessor()
    
    print("\n" + "="*70)
    print("AUTONOMOUS INSURANCE CLAIMS PROCESSING AGENT - TEST SUITE")
    print("="*70 + "\n")
    
    all_results = []
    
    for i, sample_file in enumerate(sample_files, 1):
        print(f"\n{'─'*70}")
        print(f"Processing Sample {i}: {sample_file}")
        print(f"{'─'*70}\n")
        
        try:
            result = process_text_fnol(sample_file, processor)
            all_results.append({
                'filename': sample_file,
                'result': result
            })
            
            # Display result
            print(json.dumps(result, indent=2))
            
            # Save individual result
            output_file = f"result_{i}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"✗ Error processing {sample_file}: {str(e)}")
    
    # Save all results
    with open('all_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*70)
    print("All results saved to: all_results.json")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
