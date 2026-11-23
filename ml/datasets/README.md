# ML Datasets Guide & Licensing Register

All datasets used for training and benchmarking Opportunity OS models must strictly adhere to open-source or academic permissive licensing.

## 1. Approved External Datasets
1. **ESCO Taxonomy (European Skills, Competences and Occupations):**
   - **License:** Open data under European Commission Open Data Policy (CC0 / Public Domain equivalent).
   - **Usage:** Standardized 13,800 canonical skills taxonomy.
2. **Resume Entities for NER (Kaggle):**
   - **License:** Apache 2.0 / CC BY 4.0.
   - **Usage:** Entity boundary token classification.
3. **Synthetic Indian Collegiate Resume Benchmark:**
   - **Author:** Sanju.
   - **Usage:** Indian university edge-cases (CGPA out of 10, VTU/JNTU/Anna University grading scales, regional certifications).

## 2. Privacy & PII Scrubbing Rules
- All resumes and candidate records MUST be stripped of personal identifiers (Full Name, Phone Number, Email, Student Registration ID) before saving to disk or training.
