#!/usr/bin/env python3
"""
Autonomous Insurance Claims Processing Agent
Extracts FNOL data, validates fields, and routes claims intelligently
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pdfplumber


class ClaimsProcessor:
    """
    Main claims processing agent that handles FNOL document extraction,
    validation, and routing decisions.
    """
    
    # Define mandatory fields for validation
    MANDATORY_FIELDS = [
        'policy_number',
        'policyholder_name',
        'date_of_loss',
        'location_of_loss',
        'description_of_accident',
        'claim_type'
    ]
    
    # Routing thresholds and keywords
    FAST_TRACK_THRESHOLD = 25000
    FRAUD_KEYWORDS = ['fraud', 'inconsistent', 'staged', 'suspicious', 'fabricated']
    
    def __init__(self):
        self.extracted_data = {}
        self.missing_fields = []
        self.route = ""
        self.reasoning = ""
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract all relevant information from ACORD FNOL PDF form
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted fields
        """
        extracted = {
            'policy_information': {},
            'incident_information': {},
            'involved_parties': {},
            'asset_details': {},
            'other_fields': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # Extract Policy Information
                extracted['policy_information']['policy_number'] = self._extract_field(
                    full_text, r'POLICY NUMBER[:\s]*([A-Z0-9-]+)'
                )
                extracted['policy_information']['policyholder_name'] = self._extract_field(
                    full_text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|DATE OF BIRTH)'
                )
                
                # Extract dates from policy section or date fields
                effective_date = self._extract_field(full_text, r'EFFECTIVE DATE[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
                if effective_date:
                    extracted['policy_information']['effective_date'] = effective_date
                
                # Extract Incident Information
                extracted['incident_information']['date_of_loss'] = self._extract_field(
                    full_text, r'DATE OF LOSS AND TIME[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                )
                
                # Extract time (AM/PM)
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', full_text, re.IGNORECASE)
                if time_match:
                    extracted['incident_information']['time'] = f"{time_match.group(1)} {time_match.group(2)}"
                
                # Extract location
                street = self._extract_field(full_text, r'STREET:[:\s]*([^\n]+)')
                city_state_zip = self._extract_field(full_text, r'CITY, STATE, ZIP:[:\s]*([^\n]+)')
                
                location_parts = []
                if street and street.strip():
                    location_parts.append(street.strip())
                if city_state_zip and city_state_zip.strip():
                    location_parts.append(city_state_zip.strip())
                
                extracted['incident_information']['location'] = ', '.join(location_parts) if location_parts else None
                
                # Extract description
                desc = self._extract_field(
                    full_text, 
                    r'DESCRIPTION OF ACCIDENT[:\s]*\(ACORD[^\)]*\)[:\s]*([^\n]+(?:\n(?!LOSS|DRIVER|OWNER|VEHICLE)[^\n]+)*)'
                )
                extracted['incident_information']['description'] = desc
                
                # Extract Involved Parties
                claimant = self._extract_field(
                    full_text, r'NAME OF INSURED[:\s]*\(First, Middle, Last\)[:\s]*([A-Za-z\s,\.]+?)(?:\n|INSURED)'
                )
                extracted['involved_parties']['claimant'] = claimant
                
                # Extract driver information
                driver_name = self._extract_field(
                    full_text, r"DRIVER'S NAME AND ADDRESS[:\s]*\(Check if same as insured\)[:\s]*PHONE[^\n]*\n([A-Za-z\s,\.]+?)(?:\n|PHONE)"
                )
                extracted['involved_parties']['driver_name'] = driver_name
                
                # Extract phone numbers
                phone_match = re.search(r'PHONE #[:\s]*HOME BUS CELL PRIMARY[:\s]*(\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4})', full_text)
                if phone_match:
                    extracted['involved_parties']['contact_phone'] = phone_match.group(1)
                
                # Extract email
                email = self._extract_field(full_text, r'E-MAIL ADDRESS:[:\s]*PRIMARY E-MAIL ADDRESS:[:\s]*([^\s\n]+@[^\s\n]+)')
                extracted['involved_parties']['contact_email'] = email
                
                # Extract Asset Details
                vehicle_year = self._extract_field(full_text, r'VEH #[:\s]*YEAR[:\s]*(\d{4})')
                vehicle_make = self._extract_field(full_text, r'MAKE:[:\s]*([A-Z][A-Za-z]+)')
                vehicle_model = self._extract_field(full_text, r'MODEL:[:\s]*([A-Za-z0-9\s]+?)(?:\n|BODY)')
                vin = self._extract_field(full_text, r'V\.I\.N\.:[:\s]*([A-Z0-9]{17})')
                
                extracted['asset_details']['asset_type'] = 'vehicle'
                if vehicle_year or vehicle_make or vehicle_model:
                    vehicle_desc = ' '.join(filter(None, [vehicle_year, vehicle_make, vehicle_model]))
                    extracted['asset_details']['vehicle_description'] = vehicle_desc
                
                extracted['asset_details']['asset_id'] = vin
                
                # Extract damage estimate
                estimate = self._extract_field(full_text, r'ESTIMATE AMOUNT:[:\s]*\$?([0-9,]+(?:\.\d{2})?)')
                if estimate:
                    # Clean the estimate (remove commas)
                    estimate_clean = estimate.replace(',', '')
                    try:
                        extracted['asset_details']['estimated_damage'] = float(estimate_clean)
                    except ValueError:
                        extracted['asset_details']['estimated_damage'] = None
                
                # Determine claim type
                claim_type = self._determine_claim_type(full_text)
                extracted['other_fields']['claim_type'] = claim_type
                
                # Extract Line of Business
                lob = self._extract_field(full_text, r'LINE OF BUSINESS[:\s]*([A-Z\s]+?)(?:\n|ACORD)')
                extracted['other_fields']['line_of_business'] = lob
                
                # Extract NAIC code
                naic = self._extract_field(full_text, r'CARRIER NAIC CODE[:\s]*(\d+)')
                extracted['other_fields']['naic_code'] = naic
                
        except Exception as e:
            print(f"Error extracting PDF: {str(e)}")
            
        return extracted
    
    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        """
        Extract a field using regex pattern
        
        Args:
            text: Full text to search
            pattern: Regex pattern
            
        Returns:
            Extracted value or None
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            # Clean up the value
            value = ' '.join(value.split())  # Normalize whitespace
            return value if value else None
        return None
    
    def _determine_claim_type(self, text: str) -> str:
        """
        Determine the claim type based on content
        
        Args:
            text: Full document text
            
        Returns:
            Claim type string
        """
        text_lower = text.lower()
        
        # Check for injury-related keywords
        injury_keywords = ['injury', 'injured', 'hospital', 'medical', 'ambulance', 'bodily']
        if any(keyword in text_lower for keyword in injury_keywords):
            return 'injury'
        
        # Check for property damage
        if 'property' in text_lower or 'damage' in text_lower:
            return 'property_damage'
        
        # Check for collision
        if 'collision' in text_lower or 'accident' in text_lower:
            return 'collision'
        
        # Default to auto if it's an auto form
        return 'auto'
    
    def flatten_extracted_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested extracted data for easier processing
        
        Args:
            extracted: Nested extracted data
            
        Returns:
            Flattened dictionary
        """
        flattened = {}
        
        # Policy Information
        flattened['policy_number'] = extracted['policy_information'].get('policy_number')
        flattened['policyholder_name'] = extracted['policy_information'].get('policyholder_name')
        flattened['effective_date'] = extracted['policy_information'].get('effective_date')
        
        # Incident Information
        flattened['date_of_loss'] = extracted['incident_information'].get('date_of_loss')
        flattened['time_of_loss'] = extracted['incident_information'].get('time')
        flattened['location_of_loss'] = extracted['incident_information'].get('location')
        flattened['description_of_accident'] = extracted['incident_information'].get('description')
        
        # Involved Parties
        flattened['claimant'] = extracted['involved_parties'].get('claimant')
        flattened['driver_name'] = extracted['involved_parties'].get('driver_name')
        flattened['contact_phone'] = extracted['involved_parties'].get('contact_phone')
        flattened['contact_email'] = extracted['involved_parties'].get('contact_email')
        
        # Asset Details
        flattened['asset_type'] = extracted['asset_details'].get('asset_type')
        flattened['asset_id'] = extracted['asset_details'].get('asset_id')
        flattened['vehicle_description'] = extracted['asset_details'].get('vehicle_description')
        flattened['estimated_damage'] = extracted['asset_details'].get('estimated_damage')
        
        # Other
        flattened['claim_type'] = extracted['other_fields'].get('claim_type')
        flattened['line_of_business'] = extracted['other_fields'].get('line_of_business')
        flattened['naic_code'] = extracted['other_fields'].get('naic_code')
        
        return flattened
    
    def validate_fields(self, flattened_data: Dict[str, Any]) -> List[str]:
        """
        Identify missing mandatory fields
        
        Args:
            flattened_data: Flattened extracted data
            
        Returns:
            List of missing field names
        """
        missing = []
        
        for field in self.MANDATORY_FIELDS:
            if not flattened_data.get(field):
                missing.append(field)
        
        return missing
    
    def route_claim(self, flattened_data: Dict[str, Any], missing_fields: List[str]) -> tuple:
        """
        Determine the routing decision and provide reasoning
        
        Args:
            flattened_data: Flattened extracted data
            missing_fields: List of missing mandatory fields
            
        Returns:
            Tuple of (route, reasoning)
        """
        reasons = []
        
        # Rule 1: Missing mandatory fields → Manual review
        if missing_fields:
            route = "Manual Review"
            reasons.append(f"Missing mandatory fields: {', '.join(missing_fields)}")
            return route, '; '.join(reasons)
        
        # Rule 2: Fraud indicators → Investigation Flag
        description = flattened_data.get('description_of_accident', '').lower()
        if any(keyword in description for keyword in self.FRAUD_KEYWORDS):
            route = "Investigation Queue"
            reasons.append("Description contains potential fraud indicators")
            return route, '; '.join(reasons)
        
        # Rule 3: Injury claim → Specialist Queue
        if flattened_data.get('claim_type') == 'injury':
            route = "Specialist Queue"
            reasons.append("Claim involves injury and requires specialist review")
            return route, '; '.join(reasons)
        
        # Rule 4: Estimated damage check → Fast-track or Standard
        estimated_damage = flattened_data.get('estimated_damage')
        if estimated_damage is not None:
            if estimated_damage < self.FAST_TRACK_THRESHOLD:
                route = "Fast-Track"
                reasons.append(f"Estimated damage (${estimated_damage:,.2f}) is below fast-track threshold (${self.FAST_TRACK_THRESHOLD:,})")
            else:
                route = "Standard Processing"
                reasons.append(f"Estimated damage (${estimated_damage:,.2f}) exceeds fast-track threshold (${self.FAST_TRACK_THRESHOLD:,})")
        else:
            route = "Manual Review"
            reasons.append("Estimated damage amount is missing or invalid")
        
        return route, '; '.join(reasons)
    
    def process_claim(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main processing pipeline
        
        Args:
            pdf_path: Path to FNOL PDF file
            
        Returns:
            Complete processing result in JSON format
        """
        # Extract data from PDF
        extracted = self.extract_from_pdf(pdf_path)
        
        # Flatten the data
        flattened = self.flatten_extracted_data(extracted)
        
        # Validate fields
        missing = self.validate_fields(flattened)
        
        # Route the claim
        route, reasoning = self.route_claim(flattened, missing)
        
        # Prepare output
        result = {
            "extractedFields": flattened,
            "missingFields": missing,
            "recommendedRoute": route,
            "reasoning": reasoning
        }
        
        return result


def main():
    """
    Main entry point for the claims processor
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python claims_processor.py <path_to_fnol_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print(f"\n{'='*60}")
    print("AUTONOMOUS INSURANCE CLAIMS PROCESSING AGENT")
    print(f"{'='*60}\n")
    print(f"Processing: {pdf_path}\n")
    
    # Create processor and process claim
    processor = ClaimsProcessor()
    result = processor.process_claim(pdf_path)
    
    # Display results
    print(json.dumps(result, indent=2))
    
    # Save to file
    output_file = "claim_processing_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
