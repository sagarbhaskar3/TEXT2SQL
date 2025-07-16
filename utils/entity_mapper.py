# utils/entity_mapper.py - Updated Entity Mapper
import re
import logging
from typing import Dict, List, Tuple, Optional
from config.domain_knowledge import term_mappings, known_values, healthcare_synonyms

logger = logging.getLogger(__name__)

class HealthcareEntityMapper:
    """Enhanced entity mapper for healthcare queries with multi-constraint support"""
    
    def __init__(self):
        self.synonym_patterns = self._build_synonym_patterns()
        self.location_patterns = self._build_location_patterns()
        self.temporal_patterns = self._build_temporal_patterns()
        self.medical_patterns = self._build_medical_patterns()
        
    def _build_synonym_patterns(self) -> Dict[str, List[str]]:
        """Build comprehensive synonym patterns for healthcare terms"""
        patterns = {}
        
        # Extend known synonyms
        patterns.update(healthcare_synonyms)
        
        # Add procedure-specific synonyms
        patterns["procedure"] = ["surgery", "operation", "treatment", "intervention", "therapy"]
        patterns["facility"] = ["hospital", "clinic", "center", "asc", "ambulatory", "surgical center"]
        patterns["provider"] = ["doctor", "physician", "hcp", "prescriber", "clinician"]
        patterns["medication"] = ["drug", "medicine", "pharmaceutical", "prescription"]
        
        return patterns
    
    def _build_location_patterns(self) -> Dict[str, str]:
        """Build location detection patterns"""
        # Get state names safely
        try:
            states = known_values.get("states", [])
            state_names_pattern = '|'.join([state for state in states if len(state) > 2])  # Full state names
        except Exception:
            state_names_pattern = "California|New York|Texas|Florida"  # Fallback
            
        return {
            "state_codes": r'\b([A-Z]{2})\b',
            "state_names": f'\\b({state_names_pattern})\\b',
            "cities": r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b(?=\s*,?\s*(?:' + '|'.join(known_values.get("states", [])[:10]) + '))',
            "regions": r'\b(Northeast|Southeast|Midwest|Southwest|West Coast|East Coast|Pacific Northwest)\b'
        }
    
    def _build_temporal_patterns(self) -> Dict[str, str]:
        """Build temporal detection patterns"""
        return {
            "years": r'\b(20\d{2})\b',
            "months": r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
            "quarters": r'\b(Q[1-4])\b',
            "relative_time": r'\b(last|past|previous|recent|current|this|next)\s+(year|month|quarter|week)\b'
        }
    
    def _build_medical_patterns(self) -> Dict[str, str]:
        """Build medical term detection patterns"""
        return {
            "specialties": r'\b(cardiology|oncology|endocrinology|neurology|psychiatry|orthopedics|dermatology|gastroenterology|pulmonology|rheumatology|urology|ophthalmology|otolaryngology|anesthesiology|radiology|pathology|emergency medicine|family medicine|internal medicine|pediatrics|obstetrics|gynecology)\b',
            "procedures": r'\b(laparoscopic|arthroscopy|arthroplasty|angioplasty|catheterization|endoscopy|colonoscopy|biopsy|surgery|operation|procedure|treatment)\b',
            "conditions": r'\b(diabetes|hypertension|cancer|cardiovascular|respiratory|neurological|psychiatric|orthopedic|dermatological|gastrointestinal)\b',
            "drug_classes": r'\b(insulin|statin|beta-blocker|ace inhibitor|antibiotic|antidepressant|antihypertensive|anticoagulant|immunosuppressant|chemotherapy)\b'
        }
    
    def extract_entities(self, query: str) -> Tuple[Dict, Dict]:
        """
        Enhanced entity extraction with multi-constraint support
        Returns (entities, mappings) where mappings include column assignments
        """
        
        logger.info(f"🔍 Extracting entities from query: {query}")
        
        # Initialize all entity types to prevent KeyError
        entities = {
            "drugs": [],
            "states": [],
            "cities": [],
            "procedures": [],
            "specialties": [],
            "years": [],
            "numbers": [],
            "companies": [],
            "facilities": [],
            "providers": [],
            "conditions": [],
            "payments": [],
            "patients": [],
            "payment_types": []
        }
        
        query_lower = query.lower()
        
        try:
            # Extract drugs with synonym matching
            entities["drugs"] = self._extract_drugs(query, query_lower)
            
            # Extract locations with enhanced patterns
            entities["states"], entities["cities"] = self._extract_locations(query, query_lower)
            
            # Extract temporal information
            entities["years"] = self._extract_temporal(query, query_lower)
            
            # Extract medical specialties
            entities["specialties"] = self._extract_specialties(query, query_lower)
            
            # Extract procedures with pattern matching
            entities["procedures"] = self._extract_procedures(query, query_lower)
            
            # Extract numerical constraints (for "top N" queries)
            entities["numbers"] = self._extract_numbers(query, query_lower)
            
            # Extract companies
            entities["companies"] = self._extract_companies(query, query_lower)
            
            # Extract facilities
            entities["facilities"] = self._extract_facilities(query, query_lower)
            
            # Extract provider types
            entities["providers"] = self._extract_providers(query, query_lower)
            
            # Extract conditions
            entities["conditions"] = self._extract_conditions(query, query_lower)
            
            # Extract payment types
            entities["payment_types"] = self._extract_payment_types(query, query_lower)
            
            # Extract payments (general payment terms)
            entities["payments"] = self._extract_payments(query, query_lower)
            
            # Extract patients (if any patient-related terms)
            entities["patients"] = self._extract_patients(query, query_lower)
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            # Continue with empty entities rather than failing
        
        # Build column mappings
        mappings = self._build_column_mappings(entities)
        
        # Log findings
        for entity_type, values in entities.items():
            if values:
                logger.info(f"✅ Found {entity_type}: {', '.join(map(str, values))}")
        
        mapped_count = sum(1 for entity_data in mappings.values() 
                          if isinstance(entity_data, dict) and entity_data.get('values'))
        logger.info(f"✅ Entity extraction completed. Found {mapped_count} entity types")
        
        return entities, mappings
    
    def _extract_drugs(self, query: str, query_lower: str) -> List[str]:
        """Extract drug names with brand/generic matching"""
        drugs_found = []
        
        try:
            # Check known drugs
            for drug in known_values.get("drugs", []):
                if drug.lower() in query_lower:
                    drugs_found.append(drug)
            
            # Check for drug patterns
            drug_patterns = [
                r'\b(\w+)\s*(?:tablet|capsule|injection|mg|mcg)\b',
                r'\b(?:drug|medication|medicine)\s+(\w+)\b'
            ]
            
            for pattern in drug_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    if len(match) > 3 and match.title() not in drugs_found:
                        # Check if it's likely a drug name
                        if not any(common in match.lower() for common in ['the', 'and', 'for', 'with', 'are']):
                            drugs_found.append(match.title())
        except Exception as e:
            logger.warning(f"Drug extraction failed: {e}")
        
        return list(set(drugs_found))
    
    def _extract_locations(self, query: str, query_lower: str) -> Tuple[List[str], List[str]]:
        """Extract states and cities with enhanced pattern matching"""
        states_found = []
        cities_found = []
        
        try:
            # Extract state codes
            state_codes = re.findall(self.location_patterns["state_codes"], query)
            for code in state_codes:
                if code in known_values.get("states", []):
                    states_found.append(code)
            
            # Extract state names
            try:
                state_names = re.findall(self.location_patterns["state_names"], query, re.IGNORECASE)
                for name in state_names:
                    states_found.append(name)
                    # Also add state code if known
                    state_mapping = {
                        "new york": "NY", "california": "CA", "texas": "TX", "florida": "FL",
                        "pennsylvania": "PA", "illinois": "IL", "ohio": "OH", "georgia": "GA",
                        "north carolina": "NC", "michigan": "MI"
                    }
                    if name.lower() in state_mapping:
                        states_found.append(state_mapping[name.lower()])
            except Exception:
                # Fallback pattern matching
                for state in known_values.get("states", []):
                    if len(state) > 2 and state.lower() in query_lower:
                        states_found.append(state)
            
            # Extract cities
            try:
                cities = re.findall(self.location_patterns["cities"], query, re.IGNORECASE)
                cities_found.extend(cities)
            except Exception:
                pass
            
            # Check for known cities
            known_cities = ["Austin", "Houston", "Dallas", "New York", "Los Angeles", "Chicago", "Miami", "Boston", "Seattle", "Denver"]
            for city in known_cities:
                if city.lower() in query_lower:
                    cities_found.append(city)
                    
        except Exception as e:
            logger.warning(f"Location extraction failed: {e}")
        
        return list(set(states_found)), list(set(cities_found))
    
    def _extract_temporal(self, query: str, query_lower: str) -> List[str]:
        """Extract temporal constraints"""
        years_found = []
        
        try:
            # Extract years
            years = re.findall(self.temporal_patterns["years"], query)
            years_found.extend(years)
            
            # Extract relative temporal references
            current_year = 2024
            relative_patterns = {
                "last year": str(current_year - 1),
                "previous year": str(current_year - 1),
                "this year": str(current_year),
                "current year": str(current_year),
                "2023": "2023",
                "2022": "2022",
                "2021": "2021"
            }
            
            for phrase, year in relative_patterns.items():
                if phrase in query_lower:
                    years_found.append(year)
                    
        except Exception as e:
            logger.warning(f"Temporal extraction failed: {e}")
        
        return list(set(years_found))
    
    def _extract_specialties(self, query: str, query_lower: str) -> List[str]:
        """Extract medical specialties"""
        specialties_found = []
        
        try:
            # Check known specialties
            for specialty in known_values.get("specialties", []):
                if specialty.lower() in query_lower:
                    specialties_found.append(specialty)
            
            # Pattern-based extraction
            specialty_matches = re.findall(self.medical_patterns["specialties"], query, re.IGNORECASE)
            specialties_found.extend(specialty_matches)
            
            # Handle specialty variations
            specialty_variations = {
                "cardiologist": "cardiology",
                "oncologist": "oncology",
                "endocrinologist": "endocrinology",
                "neurologist": "neurology",
                "orthopedist": "orthopedics"
            }
            
            for variation, standard in specialty_variations.items():
                if variation in query_lower:
                    specialties_found.append(standard)
                    
        except Exception as e:
            logger.warning(f"Specialty extraction failed: {e}")
        
        return list(set(specialties_found))
    
    def _extract_procedures(self, query: str, query_lower: str) -> List[str]:
        """Extract medical procedures"""
        procedures_found = []
        
        try:
            # Check known procedures
            for procedure in known_values.get("procedures", []):
                if procedure.lower() in query_lower:
                    procedures_found.append(procedure)
            
            # Pattern-based extraction
            procedure_matches = re.findall(self.medical_patterns["procedures"], query, re.IGNORECASE)
            procedures_found.extend(procedure_matches)
            
            # Specific procedure patterns
            specific_patterns = [
                r'\b(knee|hip|shoulder)\s+(replacement|arthroplasty)\b',
                r'\b(coronary|cardiac)\s+(angioplasty|catheterization)\b',
                r'\b(cataract|hernia|appendix)\s+(surgery|repair|removal)\b'
            ]
            
            for pattern in specific_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    procedure_name = ' '.join(match)
                    procedures_found.append(procedure_name)
                    
        except Exception as e:
            logger.warning(f"Procedure extraction failed: {e}")
        
        return list(set(procedures_found))
    
    def _extract_numbers(self, query: str, query_lower: str) -> List[str]:
        """Extract numerical constraints for top N queries"""
        numbers_found = []
        
        try:
            # Extract explicit numbers
            number_patterns = [
                r'\btop\s+(\d+)\b',
                r'\b(\d+)\s+(?:top|best|highest)\b',
                r'\bfirst\s+(\d+)\b',
                r'\b(\d+)\s+(?:leading|primary)\b'
            ]
            
            for pattern in number_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                numbers_found.extend(matches)
            
            # Handle word numbers
            word_numbers = {
                "five": "5", "ten": "10", "fifteen": "15", "twenty": "20",
                "few": "5", "several": "10", "many": "20"
            }
            
            for word, number in word_numbers.items():
                if word in query_lower:
                    numbers_found.append(number)
                    
        except Exception as e:
            logger.warning(f"Number extraction failed: {e}")
        
        return list(set(numbers_found))
    
    def _extract_companies(self, query: str, query_lower: str) -> List[str]:
        """Extract pharmaceutical companies"""
        companies_found = []
        
        try:
            # Check known companies
            for company in known_values.get("companies", []):
                if company.lower() in query_lower:
                    companies_found.append(company)
            
            # Pattern for company names
            company_patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Ltd|LLC|Pharmaceuticals?)\b',
                r'\b(?:pharmaceutical|pharma|biotech)\s+(?:company\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                companies_found.extend(matches)
                
        except Exception as e:
            logger.warning(f"Company extraction failed: {e}")
        
        return list(set(companies_found))
    
    def _extract_facilities(self, query: str, query_lower: str) -> List[str]:
        """Extract healthcare facilities"""
        facilities_found = []
        
        try:
            # Facility type patterns
            facility_patterns = [
                r'\b(ambulatory\s+surgical\s+center|asc)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:hospital|medical center|clinic|health system)\b',
                r'\b(?:hospital|clinic|center)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            ]
            
            for pattern in facility_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                facilities_found.extend([match for match in matches if isinstance(match, str)])
                
        except Exception as e:
            logger.warning(f"Facility extraction failed: {e}")
        
        return list(set(facilities_found))
    
    def _extract_providers(self, query: str, query_lower: str) -> List[str]:
        """Extract provider types"""
        providers_found = []
        
        provider_types = ["hcp", "doctor", "physician", "provider", "prescriber", "clinician", "specialist"]
        
        for provider_type in provider_types:
            if provider_type in query_lower:
                providers_found.append(provider_type)
        
        return list(set(providers_found))
    
    def _extract_conditions(self, query: str, query_lower: str) -> List[str]:
        """Extract medical conditions"""
        conditions_found = []
        
        try:
            # Check known conditions
            for condition in known_values.get("conditions", []):
                if condition.lower() in query_lower:
                    conditions_found.append(condition)
            
            # Pattern-based extraction
            condition_matches = re.findall(self.medical_patterns["conditions"], query, re.IGNORECASE)
            conditions_found.extend(condition_matches)
            
        except Exception as e:
            logger.warning(f"Condition extraction failed: {e}")
        
        return list(set(conditions_found))
    
    def _extract_payment_types(self, query: str, query_lower: str) -> List[str]:
        """Extract payment types"""
        payment_types_found = []
        
        try:
            # Check known payment types
            for payment_type in known_values.get("payment_types", []):
                if payment_type.lower() in query_lower:
                    payment_types_found.append(payment_type)
            
            # Payment-related terms
            payment_terms = ["consulting", "speaker", "research", "education", "travel", "food", "beverage", "honoraria"]
            
            for term in payment_terms:
                if term in query_lower:
                    payment_types_found.append(term.title())
                    
        except Exception as e:
            logger.warning(f"Payment type extraction failed: {e}")
        
        return list(set(payment_types_found))
    
    def _extract_payments(self, query: str, query_lower: str) -> List[str]:
        """Extract general payment terms"""
        payments_found = []
        
        payment_terms = ["payment", "paid", "pay", "compensation", "financial", "money", "amount"]
        
        for term in payment_terms:
            if term in query_lower:
                payments_found.append(term)
        
        return list(set(payments_found))
    
    def _extract_patients(self, query: str, query_lower: str) -> List[str]:
        """Extract patient-related terms"""
        patients_found = []
        
        patient_terms = ["patient", "patients", "individual", "case"]
        
        for term in patient_terms:
            if term in query_lower:
                patients_found.append(term)
        
        return list(set(patients_found))
    
    def _build_column_mappings(self, entities: Dict) -> Dict:
        """Build column mappings for extracted entities"""
        mappings = {}
        
        for entity_type, values in entities.items():
            if values:
                # Get column mappings from term_mappings
                columns = term_mappings.get(entity_type, [])
                
                # Add specific column mappings based on entity type
                if entity_type == "drugs":
                    columns.extend(["NDC_PREFERRED_BRAND_NM", "NDC_DRUG_NM", "NDC_GENERIC_NM", "product_name"])
                elif entity_type == "states":
                    columns.extend(["PRESCRIBER_NPI_STATE_CD", "states[1]", "primary_type_2_npi_state"])
                elif entity_type == "procedures":
                    columns.extend(["procedure_code_description", "diagnosis_code_description"])
                elif entity_type == "specialties":
                    columns.extend(["specialties[1]", "primary_specialty", "referring_specialty"])
                elif entity_type == "years":
                    columns.extend(["year", "EXTRACT(YEAR FROM date)", "EXTRACT(YEAR FROM SERVICE_DATE_DD)"])
                elif entity_type == "companies":
                    columns.extend(["life_science_firm_name", "PAYER_COMPANY_NM"])
                elif entity_type == "facilities":
                    columns.extend(["primary_hospital_name", "referring_hospital_name", "primaryOrgName"])
                elif entity_type == "payment_types":
                    columns.extend(["nature_of_payment"])
                elif entity_type == "payments":
                    columns.extend(["amount", "nature_of_payment", "TOTAL_PAID_AMT"])
                elif entity_type == "patients":
                    columns.extend(["PATIENT_ID"])
                
                mappings[entity_type] = {
                    "values": values,
                    "columns": list(set(columns))  # Remove duplicates
                }
        
        return mappings

# Standalone functions for backward compatibility
def extract_entities(query: str) -> Tuple[Dict, Dict]:
    """
    Enhanced entity extraction function for backward compatibility
    """
    try:
        mapper = HealthcareEntityMapper()
        return mapper.extract_entities(query)
    except Exception as e:
        logger.error(f"❌ Entity extraction failed: {e}")
        
        # Fallback to basic extraction
        return _basic_entity_extraction(query)

def _basic_entity_extraction(query: str) -> Tuple[Dict, Dict]:
    """Basic fallback entity extraction"""
    
    entities = {
        "drugs": [],
        "states": [],
        "years": [],
        "numbers": [],
        "specialties": [],
        "procedures": [],
        "companies": [],
        "payments": [],
        "patients": []
    }
    
    mappings = {}
    query_lower = query.lower()
    
    try:
        # Basic drug extraction
        for drug in known_values.get("drugs", []):
            if drug.lower() in query_lower:
                entities["drugs"].append(drug)
        
        # Basic state extraction
        for state in known_values.get("states", []):
            if state.lower() in query_lower:
                entities["states"].append(state)
        
        # Basic year extraction
        years = re.findall(r'\b(20\d{2})\b', query)
        entities["years"].extend(years)
        
        # Basic number extraction
        numbers = re.findall(r'\btop\s+(\d+)\b', query, re.IGNORECASE)
        entities["numbers"].extend(numbers)
        
        # Basic specialty extraction
        for specialty in known_values.get("specialties", []):
            if specialty.lower() in query_lower:
                entities["specialties"].append(specialty)
        
        # Basic procedure extraction
        for procedure in known_values.get("procedures", []):
            if procedure.lower() in query_lower:
                entities["procedures"].append(procedure)
        
        # Basic company extraction
        for company in known_values.get("companies", []):
            if company.lower() in query_lower:
                entities["companies"].append(company)
        
        # Basic payment extraction
        payment_terms = ["payment", "paid", "compensation"]
        for term in payment_terms:
            if term in query_lower:
                entities["payments"].append(term)
        
        # Basic patient extraction
        if "patient" in query_lower:
            entities["patients"].append("patient")
        
        # Build basic mappings
        for entity_type, values in entities.items():
            if values:
                columns = term_mappings.get(entity_type, [])
                mappings[entity_type] = {
                    "values": values,
                    "columns": columns
                }
    except Exception as e:
        logger.error(f"Basic entity extraction failed: {e}")
    
    return entities, mappings