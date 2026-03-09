"""
scheme_registry.py — Dynamic JSON-based scheme registry for Nyaaya.ai

Each scheme is defined declaratively with eligibility rules using operators.
Adding a new scheme = adding a JSON entry. Zero code changes needed.

Supported operators: ==, !=, >, <, >=, <=, in, not_in, exists, between
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# All scheme definitions
# ---------------------------------------------------------------------------

SCHEME_REGISTRY: list[dict[str, Any]] = [
    # ===================================================================
    # ORIGINAL 6 SCHEMES (preserved)
    # ===================================================================
    {
        "id": "widow_pension_mh",
        "name_en": "Widow Pension Scheme (Maharashtra)",
        "name_hi": "विधवा पेंशन योजना (महाराष्ट्र)",
        "type": "state",
        "state": "Maharashtra",
        "category": "pension",
        "benefit_monthly": 600,
        "benefit_onetime": 0,
        "required_documents": ["death_certificate", "aadhaar", "income_certificate", "bank_passbook"],
        "processing_weeks": 8,
        "approval_rate": 0.91,
        "confidence": 0.94,
        "application_url": "https://aaplesarkar.mahaonline.gov.in",
        "rules": [
            {"field": "marital_status", "op": "==", "value": "widow"},
            {"field": "age", "op": "between", "value": [18, 60]},
            {"field": "income", "op": "<", "value": 15000},
            {"field": "state", "op": "==", "value": "Maharashtra"},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "disability_allowance",
        "name_en": "Disability Allowance",
        "name_hi": "विकलांगता भत्ता",
        "type": "central",
        "state": None,
        "category": "disability",
        "benefit_monthly": 500,
        "benefit_onetime": 0,
        "required_documents": ["disability_cert", "aadhaar", "income_certificate"],
        "processing_weeks": 6,
        "approval_rate": 0.85,
        "confidence": 0.87,
        "application_url": "https://www.disabilityaffairs.gov.in",
        "rules": [
            {"field": "has_disability_cert", "op": "==", "value": True},
            {"field": "disability_percentage", "op": ">=", "value": 40},
            {"field": "income", "op": "<", "value": 10000},
            {"field": "age", "op": ">=", "value": 18},
        ],
    },
    {
        "id": "nrega",
        "name_en": "NREGA Employment Guarantee",
        "name_hi": "मनरेगा रोजगार गारंटी",
        "type": "central",
        "state": None,
        "category": "employment",
        "benefit_monthly": 0,
        "benefit_onetime": 20000,
        "required_documents": ["aadhaar", "village_proof", "employment_card_application"],
        "processing_weeks": 12,
        "approval_rate": 0.78,
        "confidence": 0.89,
        "application_url": "https://nrega.nic.in",
        "rules": [
            {"field": "is_rural", "op": "==", "value": True},
            {"field": "age", "op": "between", "value": [18, 65]},
            {"field": "income", "op": "<", "value": 20000},
        ],
    },
    {
        "id": "pm_kisan",
        "name_en": "PM-KISAN Samman Nidhi",
        "name_hi": "पीएम-किसान सम्मान निधि",
        "type": "central",
        "state": None,
        "category": "agriculture",
        "benefit_monthly": 500,
        "benefit_onetime": 0,
        "required_documents": ["aadhaar", "land_ownership_record", "bank_passbook", "kisan_registration"],
        "processing_weeks": 6,
        "approval_rate": 0.92,
        "confidence": 0.93,
        "application_url": "https://pmkisan.gov.in",
        "rules": [
            {"field": "life_event", "op": "==", "value": "farmer"},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "is_rural", "op": "==", "value": True},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "old_age_pension",
        "name_en": "Indira Gandhi Old Age Pension",
        "name_hi": "इंदिरा गांधी वृद्धावस्था पेंशन",
        "type": "central",
        "state": None,
        "category": "pension",
        "benefit_monthly": 500,
        "benefit_onetime": 0,
        "required_documents": ["aadhaar", "age_proof", "bpl_card", "bank_passbook"],
        "processing_weeks": 10,
        "approval_rate": 0.88,
        "confidence": 0.90,
        "application_url": "https://nsap.nic.in",
        "rules": [
            {"field": "age", "op": ">=", "value": 60},
            {"field": "income", "op": "<", "value": 10000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "ujjwala_yojana",
        "name_en": "PM Ujjwala Yojana (Free LPG)",
        "name_hi": "पीएम उज्ज्वला योजना (मुफ्त एलपीजी)",
        "type": "central",
        "state": None,
        "category": "household",
        "benefit_monthly": 0,
        "benefit_onetime": 1600,
        "required_documents": ["aadhaar", "bpl_card", "bank_passbook", "address_proof"],
        "processing_weeks": 4,
        "approval_rate": 0.94,
        "confidence": 0.91,
        "application_url": "https://www.pmujjwalayojana.com",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["widow", "married", "divorced", "separated"]},
            {"field": "income", "op": "<", "value": 15000},
            {"field": "age", "op": ">=", "value": 18},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },

    # ===================================================================
    # NEW CENTRAL SCHEMES
    # ===================================================================
    {
        "id": "ayushman_bharat_pmjay",
        "name_en": "Ayushman Bharat PM-JAY",
        "name_hi": "आयुष्मान भारत पीएम-जय",
        "type": "central",
        "state": None,
        "category": "health",
        "benefit_monthly": 0,
        "benefit_onetime": 500000,
        "required_documents": ["aadhaar", "ration_card", "income_certificate", "family_id_card"],
        "processing_weeks": 4,
        "approval_rate": 0.89,
        "confidence": 0.92,
        "application_url": "https://pmjay.gov.in",
        "rules": [
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "pm_awas_yojana_gramin",
        "name_en": "PM Awas Yojana - Gramin (Housing)",
        "name_hi": "पीएम आवास योजना - ग्रामीण (आवास)",
        "type": "central",
        "state": None,
        "category": "housing",
        "benefit_monthly": 0,
        "benefit_onetime": 120000,
        "required_documents": ["aadhaar", "bpl_card", "land_document", "bank_passbook", "photograph"],
        "processing_weeks": 24,
        "approval_rate": 0.72,
        "confidence": 0.85,
        "application_url": "https://pmayg.nic.in",
        "rules": [
            {"field": "is_rural", "op": "==", "value": True},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "sukanya_samriddhi",
        "name_en": "Sukanya Samriddhi Yojana (Girl Child Savings)",
        "name_hi": "सुकन्या समृद्धि योजना (बेटी बचत)",
        "type": "central",
        "state": None,
        "category": "education",
        "benefit_monthly": 0,
        "benefit_onetime": 0,
        "benefit_description_en": "8.2% interest rate savings account for girl child",
        "benefit_description_hi": "बेटी के लिए 8.2% ब्याज दर बचत खाता",
        "required_documents": ["aadhaar", "birth_certificate_daughter", "bank_passbook", "photograph"],
        "processing_weeks": 2,
        "approval_rate": 0.97,
        "confidence": 0.95,
        "application_url": "https://www.indiapost.gov.in",
        "rules": [
            {"field": "dependents", "op": ">", "value": 0},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "pm_matru_vandana",
        "name_en": "PM Matru Vandana Yojana (Maternity Benefit)",
        "name_hi": "पीएम मातृ वंदना योजना (मातृत्व लाभ)",
        "type": "central",
        "state": None,
        "category": "health",
        "benefit_monthly": 0,
        "benefit_onetime": 5000,
        "required_documents": ["aadhaar", "bank_passbook", "pregnancy_certificate", "mcp_card"],
        "processing_weeks": 6,
        "approval_rate": 0.90,
        "confidence": 0.88,
        "application_url": "https://pmmvy.wcd.gov.in",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["married"]},
            {"field": "age", "op": "between", "value": [18, 50]},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "national_family_benefit",
        "name_en": "National Family Benefit Scheme",
        "name_hi": "राष्ट्रीय परिवार लाभ योजना",
        "type": "central",
        "state": None,
        "category": "social_security",
        "benefit_monthly": 0,
        "benefit_onetime": 20000,
        "required_documents": ["aadhaar", "death_certificate", "bpl_card", "bank_passbook", "family_photo"],
        "processing_weeks": 8,
        "approval_rate": 0.80,
        "confidence": 0.86,
        "application_url": "https://nsap.nic.in",
        "rules": [
            {"field": "marital_status", "op": "==", "value": "widow"},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "age", "op": "between", "value": [18, 60]},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "atal_pension_yojana",
        "name_en": "Atal Pension Yojana",
        "name_hi": "अटल पेंशन योजना",
        "type": "central",
        "state": None,
        "category": "pension",
        "benefit_monthly": 1000,
        "benefit_onetime": 0,
        "benefit_description_en": "Guaranteed pension of Rs.1,000-5,000/month after age 60",
        "benefit_description_hi": "60 वर्ष के बाद Rs.1,000-5,000/माह गारंटीड पेंशन",
        "required_documents": ["aadhaar", "bank_passbook", "mobile_number"],
        "processing_weeks": 2,
        "approval_rate": 0.96,
        "confidence": 0.94,
        "application_url": "https://www.npscra.nsdl.co.in",
        "rules": [
            {"field": "age", "op": "between", "value": [18, 40]},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "pm_vishwakarma",
        "name_en": "PM Vishwakarma (Artisan Support)",
        "name_hi": "पीएम विश्वकर्मा (कारीगर सहायता)",
        "type": "central",
        "state": None,
        "category": "employment",
        "benefit_monthly": 0,
        "benefit_onetime": 15000,
        "benefit_description_en": "Rs.15K toolkit grant + Rs.3L collateral-free loan for artisans",
        "benefit_description_hi": "कारीगरों के लिए Rs.15K टूलकिट + Rs.3L बिना गारंटी लोन",
        "required_documents": ["aadhaar", "bank_passbook", "trade_certificate", "photograph"],
        "processing_weeks": 8,
        "approval_rate": 0.82,
        "confidence": 0.85,
        "application_url": "https://pmvishwakarma.gov.in",
        "rules": [
            {"field": "age", "op": ">=", "value": 18},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "stand_up_india",
        "name_en": "Stand-Up India (SC/ST/Women Entrepreneurs)",
        "name_hi": "स्टैंड-अप इंडिया (SC/ST/महिला उद्यमी)",
        "type": "central",
        "state": None,
        "category": "employment",
        "benefit_monthly": 0,
        "benefit_onetime": 1000000,
        "benefit_description_en": "Rs.10L-1Cr bank loan for SC/ST/Women entrepreneurs",
        "benefit_description_hi": "SC/ST/महिला उद्यमियों के लिए Rs.10L-1Cr बैंक लोन",
        "required_documents": ["aadhaar", "bank_passbook", "business_plan", "caste_certificate", "photograph"],
        "processing_weeks": 12,
        "approval_rate": 0.70,
        "confidence": 0.80,
        "application_url": "https://www.standupmitra.in",
        "rules": [
            {"field": "age", "op": ">=", "value": 18},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "janani_suraksha",
        "name_en": "Janani Suraksha Yojana (Safe Motherhood)",
        "name_hi": "जननी सुरक्षा योजना (सुरक्षित मातृत्व)",
        "type": "central",
        "state": None,
        "category": "health",
        "benefit_monthly": 0,
        "benefit_onetime": 1400,
        "required_documents": ["aadhaar", "bank_passbook", "mcp_card", "bpl_card"],
        "processing_weeks": 2,
        "approval_rate": 0.93,
        "confidence": 0.91,
        "application_url": "https://nhm.gov.in",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["married"]},
            {"field": "age", "op": "between", "value": [18, 50]},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },

    # ===================================================================
    # NEW STATE SCHEMES
    # ===================================================================
    {
        "id": "karnataka_gruha_lakshmi",
        "name_en": "Karnataka Gruha Lakshmi",
        "name_hi": "कर्नाटक गृह लक्ष्मी",
        "type": "state",
        "state": "Karnataka",
        "category": "social_security",
        "benefit_monthly": 2000,
        "benefit_onetime": 0,
        "required_documents": ["aadhaar", "ration_card", "bank_passbook", "household_proof"],
        "processing_weeks": 6,
        "approval_rate": 0.88,
        "confidence": 0.90,
        "application_url": "https://sevasindhuservices.karnataka.gov.in",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["married", "widow", "divorced", "separated"]},
            {"field": "state", "op": "==", "value": "Karnataka"},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "tn_kalaignar_magalir",
        "name_en": "TN Kalaignar Magalir Urimai Thogai",
        "name_hi": "तमिलनाडु कलैगनार महिला उरिमई तोगई",
        "type": "state",
        "state": "Tamil Nadu",
        "category": "social_security",
        "benefit_monthly": 1000,
        "benefit_onetime": 0,
        "required_documents": ["aadhaar", "ration_card", "bank_passbook", "family_card"],
        "processing_weeks": 4,
        "approval_rate": 0.90,
        "confidence": 0.88,
        "application_url": "https://www.tn.gov.in",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["married", "widow", "divorced", "separated"]},
            {"field": "state", "op": "==", "value": "Tamil Nadu"},
            {"field": "age", "op": ">=", "value": 21},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "bihar_kanya_utthan",
        "name_en": "Bihar Mukhyamantri Kanya Utthan Yojana",
        "name_hi": "बिहार मुख्यमंत्री कन्या उत्थान योजना",
        "type": "state",
        "state": "Bihar",
        "category": "education",
        "benefit_monthly": 0,
        "benefit_onetime": 50000,
        "required_documents": ["aadhaar", "marksheet", "bank_passbook", "college_id", "photograph"],
        "processing_weeks": 8,
        "approval_rate": 0.85,
        "confidence": 0.87,
        "application_url": "https://ekalyan.bih.nic.in",
        "rules": [
            {"field": "state", "op": "==", "value": "Bihar"},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
    {
        "id": "mp_ladli_behna",
        "name_en": "MP Ladli Behna Yojana",
        "name_hi": "मध्य प्रदेश लाडली बहना योजना",
        "type": "state",
        "state": "Madhya Pradesh",
        "category": "social_security",
        "benefit_monthly": 1250,
        "benefit_onetime": 0,
        "required_documents": ["aadhaar", "samagra_id", "bank_passbook", "photograph"],
        "processing_weeks": 4,
        "approval_rate": 0.92,
        "confidence": 0.91,
        "application_url": "https://ladlibahna.mp.gov.in",
        "rules": [
            {"field": "marital_status", "op": "in", "value": ["married", "widow", "divorced", "separated"]},
            {"field": "state", "op": "==", "value": "Madhya Pradesh"},
            {"field": "age", "op": "between", "value": [21, 60]},
            {"field": "income", "op": "<", "value": 200000},
            {"field": "has_aadhaar", "op": "==", "value": True},
        ],
    },
]


# ---------------------------------------------------------------------------
# Mutual exclusivity rules: (scheme_a, scheme_b) → winner_id
# ---------------------------------------------------------------------------

MUTUAL_EXCLUSIONS: dict[tuple[str, str], str] = {
    ("widow_pension_mh", "old_age_pension"): "widow_pension_mh",
    ("disability_allowance", "old_age_pension"): "disability_allowance",
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_scheme_by_id(scheme_id: str) -> dict[str, Any] | None:
    """Find a scheme by its ID."""
    for s in SCHEME_REGISTRY:
        if s["id"] == scheme_id:
            return s
    return None


def get_all_scheme_ids() -> list[str]:
    """Return all scheme IDs."""
    return [s["id"] for s in SCHEME_REGISTRY]


def get_schemes_for_state(state: str | None) -> list[dict[str, Any]]:
    """Return all central schemes + state-specific schemes for the given state."""
    result = []
    for s in SCHEME_REGISTRY:
        if s["type"] == "central" or (s["state"] and state and s["state"].lower() == state.lower()):
            result.append(s)
    return result
