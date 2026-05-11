import re

class GovernanceEngine:
    """
    Automated Governance Rule Engine for Sensitive Data Detection
    """
    
    # Common Patterns (Regex)
    PATTERNS = {
        "Email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        "Phone": r"^\+?[1-9]\d{1,14}$",
        "Aadhaar": r"^[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}$|(?<![0-9])[2-9]{1}[0-9]{11}(?![0-9])"
    }
    
    # Metadata Keywords (Column Names)
    RULES = {
        "PII": ["email", "mail", "phone", "mobile", "tel", "contact", "address", "addr", "dob", "birth", "gender", "name", "fname", "lname"],
        "Confidential": ["salary", "ssn", "aadhaar", "pan", "passport", "tax", "income", "credit", "card", "bank", "account"],
        "Identifier": ["id", "guid", "uuid", "pk", "key", "reference", "ref", "code"]
    }

    @staticmethod
    def detect_category(name, sample_value=None):
        """
        Analyzes a column name (and optional sample value) to suggest a classification.
        Returns: (Classification, Confidence, Reason)
        """
        name_lower = name.lower().replace("_", "").replace(" ", "")
        
        # 1. Rule Check: Aadhaar (Highest Priority)
        if "aadhaar" in name_lower or "adhar" in name_lower:
            return "Confidential", 100, "Metadata Match: Aadhaar"
        
        # 2. Rule Check: Email & Phone (High Priority PII)
        if any(kw in name_lower for kw in ["email", "mail"]):
            return "PII", 95, "Metadata Match: Email"
        
        if any(kw in name_lower for kw in ["phone", "mobile", "tel", "contact"]):
            return "PII", 95, "Metadata Match: Phone/Contact"

        # 3. Rule Check: PII General
        for keyword in GovernanceEngine.RULES["PII"]:
            if keyword in name_lower:
                return "PII", 85, f"Metadata Match: {keyword.capitalize()}"

        # 4. Rule Check: Confidential General
        for keyword in GovernanceEngine.RULES["Confidential"]:
            if keyword in name_lower:
                return "Confidential", 90, f"Metadata Match: {keyword.capitalize()}"

        # 5. Rule Check: Identifiers
        for keyword in GovernanceEngine.RULES["Identifier"]:
            if keyword in name_lower:
                return "Internal", 80, f"Metadata Match: {keyword.capitalize()}"

        # 6. Sample Value Check (if provided)
        if sample_value:
            s_val = str(sample_value).strip()
            if re.match(GovernanceEngine.PATTERNS["Email"], s_val):
                return "PII", 100, "Regex Match: Email Pattern"
            if re.match(GovernanceEngine.PATTERNS["Phone"], s_val):
                return "PII", 90, "Regex Match: Phone Pattern"
            if re.match(GovernanceEngine.PATTERNS["Aadhaar"], s_val):
                return "Confidential", 100, "Regex Match: Aadhaar Pattern"

        return "Internal", 0, "No standard pattern found"

    @classmethod
    def process_suggestions(cls, suggestions, apply_classification=True):
        """
        Overlay automated rules on top of AI suggestions.
        apply_classification: if False, skip writing classification/governance_tags.
        """
        for s in suggestions:
            col_name = s.get('related_column', '')
            if not col_name and s.get('type') == 'Table':
                col_name = s.get('display_column', '')

            if col_name and apply_classification:
                auto_cls, auto_conf, reason = cls.detect_category(col_name)

                # If rule engine is very confident, override AI or mark for review
                if auto_conf >= 90:
                    current_cls = s.get('classification', 'Internal')
                    if current_cls != auto_cls:
                        s['classification'] = auto_cls
                        s['governance_tags'] = f"Auto: {reason}"
                        # Increase confidence if it matches
                        s['confidence_score'] = max(s.get('confidence_score', 0), auto_conf)

        return suggestions
