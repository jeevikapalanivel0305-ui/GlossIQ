import re

# Domain Specific Knowledge Bases
DOMAIN_PATTERNS = {
    "Healthcare": ["dr", "pt", "hosp", "diag", "pat", "phys", "med", "clin", "dose", "rx"],
    "Finance": ["acc", "bal", "txn", "rev", "cost", "amt", "bank", "credit", "debt", "loan", "card"],
    "Retail": ["prod", "sku", "qty", "ord", "sale", "inv", "store", "ship", "return", "cart"],
    "HR": ["emp", "sal", "hiring", "dept", "job", "hr", "bonus", "leave", "pay"],
    "Manufacturing": ["part", "lot", "serial", "mfg", "line", "plant", "unit", "spec", "manuf"]
}

CONCEPT_MAPPING = {
    # Entities
    "cust": "Customer", "addr": "Address", "txn": "Transaction", "ord": "Order",
    "prod": "Product", "emp": "Employee", "org": "Organization", "acc": "Account",
    "loc": "Location", "geo": "Geography", "dept": "Department", "br": "Branch",
    # Attributes
    "id": "Identifier", "num": "Number", "cd": "Code", "key": "Key", "uid": "Unique ID",
    "nm": "Name", "fullname": "Full Name", "fname": "First Name", "lname": "Last Name",
    "amt": "Amount", "val": "Value", "bal": "Balance", "cost": "Cost", "price": "Price",
    "dt": "Date", "tm": "Time", "ts": "Timestamp", "yr": "Year", "mth": "Month",
    "desc": "Description", "txt": "Text", "cmt": "Comment", "rem": "Remarks",
    "sts": "Status", "ind": "Indicator", "flg": "Flag", "cat": "Category", "typ": "Type",
    "qty": "Quantity", "vol": "Volume", "uom": "Unit of Measure",
    "phone": "Phone Number", "tel": "Telephone", "mob": "Mobile Number",
    "eml": "Email Address", "email": "Email Address", "url": "Website Address",
    "zip": "Postal Code", "postal": "Postal Code", "city": "City Name", "st": "State Code",
}

# Governance Rulebook
CLASSIFICATION_RULES = {
    "Sensitive - PII": ["name", "email", "phone", "addr", "ssn", "birth", "dob", "tel", "mob", "pass", "pwd"],
    "Confidential": ["salary", "bal", "amt", "cost", "price", "revenue", "profit", "acc", "bank", "secret"],
    "Internal": ["id", "cd", "key", "sts", "typ", "cat", "dept", "org", "br"],
    "Public": ["desc", "txt", "cmt", "rem", "dt", "yr", "mth", "vol", "qty"]
}

def infer_domain(all_columns):
    """Adaptive Intelligence: Analyze all columns together to infer the data domain"""
    scores = {domain: 0 for domain in DOMAIN_PATTERNS}
    all_text = "_".join(all_columns).lower()
    
    for domain, keywords in DOMAIN_PATTERNS.items():
        for k in keywords:
            if re.search(fr'\b{k}\b', all_text) or f"_{k}" in all_text or f"{k}_" in all_text:
                scores[domain] += 1
                
    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] > 0 else "General"

def decompose_field_name(name):
    """Split column names by underscore, camelCase, etc"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    parts = re.split(r'[_\-\.]', s2)
    return [p for p in parts if p]

def assemble_governance(field_name, domain="General", business_context="", item_type="Column"):
    """Heuristic Generation Engine with Context Injection"""
    parts = decompose_field_name(field_name)
    concept_parts = [CONCEPT_MAPPING.get(p, p.title()) for p in parts]
    
    # 1. Assembly Term
    if item_type == "Table":
        term = " ".join(concept_parts) + " Dataset"
    else:
        final_parts = []
        for p in concept_parts:
            if not final_parts or p != final_parts[-1]:
                final_parts.append(p)
        term = " ".join(final_parts)

    # 2. Adaptive Definition Generation
    main_subject = concept_parts[0] if concept_parts else "Item"
    attribute_type = concept_parts[-1] if len(concept_parts) > 1 else "data point"
    
    base_def = f"The formal {attribute_type.lower()} associated with the {main_subject.lower()} entity."
    
    # Inject Domain Energy
    domain_suffix = ""
    if domain == "Finance": domain_suffix = " crucial for financial auditing and reconciliation."
    elif domain == "Healthcare": domain_suffix = " utilized in clinical patient management and care standards."
    elif domain == "Retail": domain_suffix = " supporting sales operations and inventory tracking."
    elif domain == "HR": domain_suffix = " representing official human resources organizational data."
    
    # Inject Business Context (Learning Layer)
    context_prefix = ""
    if business_context and len(business_context) > 5:
        # Simplified context extraction: use the first meaningful sentence or phrase
        clean_ctx = business_context.split('.')[0].strip()
        context_prefix = f"In the context of {clean_ctx.lower()}, this attribute represents "
        base_def = base_def.replace("The formal ", "")

    definition = f"{context_prefix}{base_def}{domain_suffix}"

    # 3. Governance Labels
    classification = "Internal"
    tags = set([f"Domain: {domain}", "Heuristic AI"])
    
    field_lower = field_name.lower()
    for cls, keywords in CLASSIFICATION_RULES.items():
        if any(k in field_lower for k in keywords):
            classification = cls
            break
    
    # 4. Confidence Calculation (Heuristic)
    confidence = 70
    if any(p in CONCEPT_MAPPING for p in parts): confidence = 95
    elif domain != "General": confidence = 85

    return {
        "name": term,
        "description": definition,
        "classification": classification,
        "tags": ", ".join(sorted(list(tags))),
        "type": item_type,
        "related_column": field_name if item_type == "Column" else "",
        "confidence_score": confidence
    }

def generate_internal_governance(table_name, columns, business_context=""):
    """Primary Entry Point: The Intelligent Local Model"""
    recommendations = []
    
    # Phase 1: Context Awareness (Inference)
    detected_domain = infer_domain(columns + [table_name])
    
    # Phase 2: Generation
    # Table Level
    recommendations.append(assemble_governance(table_name, domain=detected_domain, business_context=business_context, item_type="Table"))
    
    # Column Level
    for col in columns:
        recommendations.append(assemble_governance(col, domain=detected_domain, business_context=business_context, item_type="Column"))
        
    return recommendations
