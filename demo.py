#!/usr/bin/env python3
"""
Interactive Demo of Insurance Claims Processing Agent
Demonstrates key features with visual output
"""

import json
from claims_processor import ClaimsProcessor


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def print_section(text):
    """Print a section divider"""
    print("\n" + "-"*80)
    print(f"  {text}")
    print("-"*80)


def print_field(label, value, indent=2):
    """Print a labeled field"""
    spaces = " " * indent
    if value:
        print(f"{spaces}{label}: {value}")
    else:
        print(f"{spaces}{label}: [MISSING]")


def demo_extraction(processor, sample_file):
    """Demonstrate field extraction"""
    print_section("📄 FIELD EXTRACTION")
    
    # Process the file
    with open(sample_file, 'r') as f:
        text = f.read()
    
    # Extract policy info
    policy_num = processor._extract_field(text, r'POLICY NUMBER[:\s]*([A-Z0-9-]+)')
    print_field("Policy Number", policy_num)
    
    name = processor._extract_field(text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|INSURED)')
    print_field("Policyholder", name)
    
    date = processor._extract_field(text, r'DATE OF LOSS AND TIME[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
    print_field("Loss Date", date)
    
    estimate = processor._extract_field(text, r'ESTIMATE AMOUNT:[:\s]*\$?([0-9,]+(?:\.\d{2})?)')
    print_field("Damage Estimate", f"${estimate}" if estimate else None)
    
    return text


def demo_validation(text, processor):
    """Demonstrate field validation"""
    print_section("✅ FIELD VALIDATION")
    
    # Extract and flatten data
    extracted = processor.extract_from_pdf.__wrapped__(processor, None)  # Mock
    # Simulate by processing text
    extracted = {
        'policy_information': {
            'policy_number': processor._extract_field(text, r'POLICY NUMBER[:\s]*([A-Z0-9-]+)')
        },
        'incident_information': {},
        'involved_parties': {},
        'asset_details': {},
        'other_fields': {}
    }
    
    flattened = processor.flatten_extracted_data(extracted)
    missing = processor.validate_fields(flattened)
    
    print(f"  Total Fields Checked: {len(processor.MANDATORY_FIELDS)}")
    print(f"  Missing Fields: {len(missing)}")
    
    if missing:
        print("\n  ⚠️  Missing Fields:")
        for field in missing:
            print(f"    - {field}")
    else:
        print("\n  ✓ All mandatory fields present")


def demo_routing(sample_file, processor):
    """Demonstrate routing decision"""
    print_section("🎯 ROUTING DECISION")
    
    result = None
    with open(sample_file, 'r') as f:
        text = f.read()
    
    # Simulate full processing
    extracted = {
        'policy_information': {
            'policy_number': processor._extract_field(text, r'POLICY NUMBER[:\s]*([A-Z0-9-]+)'),
            'policyholder_name': processor._extract_field(text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|INSURED)')
        },
        'incident_information': {
            'date_of_loss': processor._extract_field(text, r'DATE OF LOSS AND TIME[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'),
            'location': processor._extract_field(text, r'CITY, STATE, ZIP:[:\s]*([^\n]+)'),
            'description': processor._extract_field(text, r'DESCRIPTION OF ACCIDENT[:\s]*([^\n]+(?:\n(?!INSURED VEHICLE|DRIVER)[^\n]+)*)')
        },
        'involved_parties': {},
        'asset_details': {
            'estimated_damage': None
        },
        'other_fields': {
            'claim_type': processor._determine_claim_type(text)
        }
    }
    
    # Get damage estimate
    estimate = processor._extract_field(text, r'ESTIMATE AMOUNT:[:\s]*\$?([0-9,]+(?:\.\d{2})?)')
    if estimate:
        extracted['asset_details']['estimated_damage'] = float(estimate.replace(',', ''))
    
    flattened = processor.flatten_extracted_data(extracted)
    missing = processor.validate_fields(flattened)
    route, reasoning = processor.route_claim(flattened, missing)
    
    print(f"  Route: {route}")
    print(f"  Reasoning: {reasoning}")
    
    # Show route icon
    route_icon = {
        "Fast-Track": "🚀",
        "Manual Review": "👤",
        "Investigation Queue": "🔍",
        "Specialist Queue": "⚕️",
        "Standard Processing": "📋"
    }
    
    print(f"\n  {route_icon.get(route, '📌')} Claim will be sent to: {route}")


def demo_complete_flow(sample_file):
    """Demonstrate complete processing flow"""
    print_header("AUTONOMOUS INSURANCE CLAIMS PROCESSING - DEMO")
    
    print(f"📁 Processing: {sample_file}\n")
    
    processor = ClaimsProcessor()
    
    # Step 1: Extraction
    text = demo_extraction(processor, sample_file)
    
    # Step 2: Validation
    demo_validation(text, processor)
    
    # Step 3: Routing
    demo_routing(sample_file, processor)
    
    print("\n" + "="*80 + "\n")


def run_all_demos():
    """Run demos for all sample files"""
    samples = [
        ('sample_fnol_1.txt', 'Low-Value Property Damage'),
        ('sample_fnol_2.txt', 'Potential Fraud Case'),
        ('sample_fnol_3.txt', 'Injury Claim')
    ]
    
    for i, (filename, description) in enumerate(samples, 1):
        print(f"\n{'#'*80}")
        print(f"  DEMO {i}: {description}")
        print(f"{'#'*80}")
        demo_complete_flow(filename)
        
        if i < len(samples):
            input("\nPress Enter to continue to next demo...")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         AUTONOMOUS INSURANCE CLAIMS PROCESSING AGENT - DEMO                ║
║                                                                            ║
║  This demo showcases the key capabilities of the claims processing system: ║
║                                                                            ║
║  1. 📄 Field Extraction - Extract key data from FNOL documents            ║
║  2. ✅ Validation - Identify missing or inconsistent information           ║
║  3. 🎯 Intelligent Routing - Route claims to appropriate workflows         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start the demo...")
    run_all_demos()
    
    print("\n" + "="*80)
    print("  DEMO COMPLETED")
    print("="*80)
    print("\nFor full JSON output, run: python test_claims.py")
    print("For single document processing: python claims_processor.py <file.pdf>")
    print()
