# Insurance Claims Processing Agent - Project Structure

## Directory Layout

```
insurance-claims-processor/
│
├── README.md                    # Project overview and quick start guide
├── APPROACH.md                  # Detailed design and implementation approach
├── PROJECT_STRUCTURE.md         # This file - project organization
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore patterns
│
├── claims_processor.py          # Main processing agent (core logic)
├── test_claims.py              # Test suite with multiple scenarios
├── demo.py                     # Interactive demonstration script
│
├── samples/                    # Sample FNOL documents
│   ├── sample_fnol_1.txt       # Complete claim - Fast-track scenario
│   ├── sample_fnol_2.txt       # Incomplete claim - Fraud scenario
│   └── sample_fnol_3.txt       # Injury claim - Specialist scenario
│
└── outputs/                    # Generated results
    ├── result_1.json           # Sample 1 processing result
    ├── result_2.json           # Sample 2 processing result
    ├── result_3.json           # Sample 3 processing result
    └── all_results.json        # Combined results from test suite

```

## File Descriptions

### Core Files

#### claims_processor.py (16KB)
**Purpose**: Main claims processing agent with extraction, validation, and routing logic

**Key Classes**:
- `ClaimsProcessor`: Main agent class

**Key Methods**:
- `extract_from_pdf()`: Extract fields from PDF documents
- `validate_fields()`: Check for missing mandatory fields
- `route_claim()`: Determine routing decision with reasoning
- `process_claim()`: Main pipeline orchestration

**Usage**:
```bash
python claims_processor.py <path_to_fnol.pdf>
```

#### test_claims.py (6KB)
**Purpose**: Automated test suite for processing multiple FNOL documents

**Features**:
- Processes all sample documents
- Generates individual and combined JSON outputs
- Validates extraction accuracy
- Tests all routing scenarios

**Usage**:
```bash
python test_claims.py
```

**Output**: 
- Individual result files (result_1.json, result_2.json, etc.)
- Combined results (all_results.json)

#### demo.py (7KB)
**Purpose**: Interactive demonstration of system capabilities

**Features**:
- Visual step-by-step processing
- Explains extraction, validation, and routing
- User-friendly output formatting
- Educational tool for stakeholders

**Usage**:
```bash
python demo.py
```

### Documentation Files

#### README.md (11KB)
**Contents**:
- Project overview and objectives
- Quick start guide
- Feature descriptions
- Routing rules explanation
- Architecture diagram
- Usage examples
- Configuration options
- Future enhancements roadmap

**Audience**: Developers, product managers, users

#### APPROACH.md (17KB)
**Contents**:
- Detailed design decisions
- Technical trade-offs
- Architecture deep-dive
- Routing logic explanation
- Testing strategy
- Performance analysis
- Future enhancement plans

**Audience**: Technical team, architects, reviewers

#### PROJECT_STRUCTURE.md (This file)
**Contents**:
- Directory organization
- File descriptions
- Usage guides
- Integration instructions

**Audience**: New developers, deployment engineers

### Sample Files

#### sample_fnol_1.txt (1.9KB)
**Scenario**: Complete, low-value property damage claim
- All mandatory fields present
- Damage: $4,500
- Expected Route: Fast-Track
- Key Features: Clean data, single-vehicle, no injuries

#### sample_fnol_2.txt (593B)
**Scenario**: Incomplete claim with fraud indicators
- Several missing fields
- Damage: $32,000
- Contains "inconsistent" keyword
- Expected Route: Investigation Queue
- Key Features: Fraud detection, missing data

#### sample_fnol_3.txt (1.4KB)
**Scenario**: Complete injury claim
- All fields present
- Damage: $18,500
- Involves bodily injury
- Expected Route: Specialist Queue
- Key Features: Injury detection, hospital transport

### Output Files

All output files follow this JSON structure:

```json
{
  "extractedFields": {
    "policy_number": "...",
    "policyholder_name": "...",
    "date_of_loss": "...",
    "location_of_loss": "...",
    "description_of_accident": "...",
    "estimated_damage": 0.0,
    "claim_type": "...",
    ...
  },
  "missingFields": ["field1", "field2"],
  "recommendedRoute": "Route Name",
  "reasoning": "Explanation for routing decision"
}
```

## Dependencies

### Python Version
- Python 3.8 or higher

### Required Libraries
```
pdfplumber==0.11.0    # PDF text extraction with layout preservation
pypdf==4.0.1          # PDF manipulation (backup/alternative)
reportlab==4.0.9      # PDF generation (future use)
```

### Installation
```bash
pip install -r requirements.txt
```

## Usage Workflows

### Workflow 1: Process Single Document
```bash
# Process a specific FNOL PDF
python claims_processor.py path/to/document.pdf

# Output: claim_processing_result.json
```

### Workflow 2: Run Test Suite
```bash
# Process all sample documents
python test_claims.py

# Outputs:
# - result_1.json
# - result_2.json  
# - result_3.json
# - all_results.json
```

### Workflow 3: Interactive Demo
```bash
# Run visual demonstration
python demo.py

# Interactive step-by-step walkthrough
```

### Workflow 4: Batch Processing (Future)
```bash
# Process multiple documents
python claims_processor.py --batch path/to/folder/

# Or using the test framework
python test_claims.py --directory path/to/claims/
```

## Integration Guide

### As a Module

```python
from claims_processor import ClaimsProcessor

# Initialize processor
processor = ClaimsProcessor()

# Process a claim
result = processor.process_claim("path/to/fnol.pdf")

# Access results
print(f"Route: {result['recommendedRoute']}")
print(f"Missing: {result['missingFields']}")
print(f"Reason: {result['reasoning']}")
```

### As a Service

```python
from flask import Flask, request, jsonify
from claims_processor import ClaimsProcessor

app = Flask(__name__)
processor = ClaimsProcessor()

@app.route('/process', methods=['POST'])
def process_claim():
    file = request.files['fnol']
    file.save('temp.pdf')
    result = processor.process_claim('temp.pdf')
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

### As a CLI Tool

```bash
# Make executable
chmod +x claims_processor.py

# Add shebang to file
#!/usr/bin/env python3

# Use as command
./claims_processor.py document.pdf
```

## Configuration

### Adjusting Routing Rules

Edit `claims_processor.py`:

```python
class ClaimsProcessor:
    # Fast-track threshold
    FAST_TRACK_THRESHOLD = 25000  # Change to desired amount
    
    # Fraud detection keywords
    FRAUD_KEYWORDS = [
        'fraud', 
        'inconsistent', 
        'staged',
        # Add more keywords
    ]
    
    # Mandatory fields
    MANDATORY_FIELDS = [
        'policy_number',
        'policyholder_name',
        # Add/remove fields
    ]
```

### Environment Variables (Future)

```bash
export CLAIMS_FAST_TRACK_THRESHOLD=30000
export CLAIMS_ENABLE_OCR=true
export CLAIMS_LOG_LEVEL=DEBUG
```

## Testing

### Unit Tests (Future)
```bash
pytest tests/test_extraction.py
pytest tests/test_routing.py
pytest tests/test_validation.py
```

### Integration Tests
```bash
python test_claims.py  # Current implementation
```

### Coverage Report (Future)
```bash
pytest --cov=claims_processor --cov-report=html
```

## Deployment

### Local Development
```bash
git clone <repository>
cd insurance-claims-processor
pip install -r requirements.txt
python test_claims.py
```

### Production (Future)

#### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "claims_processor.py"]
```

#### AWS Lambda
```bash
# Package dependencies
pip install -r requirements.txt -t package/
cd package && zip -r ../lambda.zip .
cd .. && zip -g lambda.zip claims_processor.py

# Deploy to Lambda
aws lambda create-function \
  --function-name ClaimsProcessor \
  --zip-file fileb://lambda.zip \
  --handler claims_processor.lambda_handler \
  --runtime python3.9
```

## Maintenance

### Adding New Form Types

1. Add extraction patterns in `_extract_field()` method
2. Update `MANDATORY_FIELDS` if needed
3. Add test cases in `test_claims.py`
4. Document changes in README.md

### Updating Routing Rules

1. Modify rule logic in `route_claim()` method
2. Update `APPROACH.md` with rationale
3. Add test case for new rule
4. Update documentation

### Adding New Features

1. Create feature branch
2. Implement in appropriate module
3. Add tests
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues

**Issue**: PDF extraction fails
**Solution**: Check if PDF is scanned (need OCR) or encrypted

**Issue**: Missing fields not detected
**Solution**: Verify field is in `MANDATORY_FIELDS` list

**Issue**: Wrong routing decision
**Solution**: Check rule priority in `route_claim()` method

**Issue**: Slow processing
**Solution**: Check PDF file size, optimize pattern matching

## Support

For issues or questions:
1. Check README.md for usage guides
2. Review APPROACH.md for design details
3. Examine sample files for examples
4. Check output JSONs for expected format

## Version History

- **v1.0.0** (2026-02-09): Initial release
  - Core extraction, validation, routing
  - Three sample scenarios
  - Comprehensive documentation
  - Test suite and demo

## License

Created for Synapx Technical Assessment

---

**Last Updated**: 2026-02-09
**Maintainer**: Assessment Submission
