# Charlson Comorbidity Index (CCI) Calculator
## Introduction
The Charlson Comorbidity Index is a widely used tool for predicting the risk of mortality or serious outcomes for an event based on the presence and severity of comorbid conditions. It was first developed with an intention to stratify the patient risk groups in clinical trials to better predict the impact of the studied disease and therapy on the patients mortailty.

Over the years there have been many iterations and modifications of the original CCI. One that gained popularity is a midification by Deyo and it is the one used in this tool.

The categories in the Deyo's modification of the Charlson Comorbidity score and the points they score are as follows:

| Category                                   | Score |
|--------------------------------------------|-------|
| Myocardial infarction                      | 1     |
| Congestive heart failure                   | 1     |
| Peripheral vascular disease                | 1     |
| Cerebrovascular disease                    | 1     |
| Dementia                                   | 1     |
| Chronic pulmonary disease                  | 1     |
| Rheumatologic disease                      | 1     |
| Peptic ulcer disease                       | 1     |
| Mild liver disease                         | 1     |
| Diabetes                                   | 1     |
| Diabetes with chronic complications        | 2     |
| Hemiplegia or paraplegia                   | 2     |
| Renal disease                              | 2     |
| Any malignancy including leukemia and lymphoma | 2 |
| Moderate or severe liver disease           | 3     |
| Metastatic solid tumor                     | 6     |
| HIV/AIDS                                   | 6     |


This package allows calculation of CCI based on ICD-Codes.

## Installation

## Usage
The main function of the package, calculate_score, can be imported from the package as follows:
from cci_calculator import calculate_score
The function calculate_score takes in 3 arguments:
- icd_codes - a string or a list of strings with the ICD-10 codes from the patients' diagnoses
- mapping - a string, which mapping to use for the calculation
- exact_code - a boolean

### icd_codes
The ICD-10 codes, meaning diagnoses of a single patient. These are used to decide which of categories mentioned in the Introduction score points.
### mapping
Identifier for the version of the ICD code mapping to be used. Valid options for the current version inculde:
- "icd2024gm" : the 2024 version of the German Modification ICD-10 codes, mapped by the algorithm authors
- "icd2024gm_quan": a variation based on Quan's implementation, applied to the 2024 ICD-10 GM codes.
- "icd2024_quan_orig" : Quan's mapping, as presented and explained in the following paper , DOI: 10.1097/01.mlr.0000182534.19832.83


This argument is optional, by default it is set to "icd2024gm".
### exact_codes
If True, checks for exact matches between ICD codes and the mapping data. If False, checks for prefix matches. Default is False, meaning that if any of the codes in the input start with any of the codes in the selected mapping list it scores.
Example: In the selected mapping, there is a code 'K70.48' for 'Other unspecified alcoholic liver failure'. The code is listed under the category 'severe liver disease' and scores 3 points. If in the input a code 'K70.4811' is provided, it still scores 3 points, as it starts with 'K70.48'. This was implemented as a means of ensuring that if any of the codes is extended with subcodes, they all still score points even if not all are yet implemented in the package's library.
### Output
The output is a tuple.
The first element is an integer, ranging from 0 to 29, and meaning the total scored points. 
The second element is a list of the categories that scored points when calculating the score.

## Mapping logic
The mapping is stored in a JSON file. It organizes ICD-10 codes into categories representing different comorbidities (see Table in the Introduction section). Each category has attributes such as:
- condition: ('any' or 'both') Specifies if scoring should occur when any code from the list matches, or if both subgroups of codes must match (useful for complex conditions with multiple subgroups).
- codes: A list of ICD codes or groups of codes. Each code (or group) can either match exactly or by prefix, depending on the function’s input parameter (see Usage)
- weight: Points scored by the category. Each category has a weight that adds to the total score if the condition is met.
- depends_on: Specifies dependencies among categories, ensuring only the more severe condition scores if both are present (e.g., severe liver disease supersedes mild liver disease).

Example structure:
{
    "icd2024gm": {
        "myocardial_infarction": {
            "condition": "any",
            "codes": ["I21", "I22"],
            "weight": 1
        },
        "diabetes": {
            "condition": "any",
            "codes": ["E10", "E11"],
            "weight": 1,
            "depends_on": ["diabetes_complicated"]
        },
        "diabetes_complicated": {
            "condition": "any",
            "codes": ["E13"],
            "weight": 2
        }
    }
}

By implementing this structure it was possible to make the package flexible in terms of updating the mapping data. Adding, extending, or modifying the current mappings can be done by changing only the JSON file and without changing the core code.


## About current mappings
- "icd2024_quan_orig" : Quan's original mapping, as presented and explained in the following paper , DOI: 10.1097/01.mlr.0000182534.19832.83
- "icd2024gm" : the 2024 version of the German Modification ICD-10 codes, mapped by the algorithm authors. It was prepared by two authors independently assigning ICD-10 codes from the 2024 German Modification list to each of the categories. In case when inconsistencies were present, these were discussed until a consensus was found.
- "icd2024gm_quan": a variation based on Quan's implementation, applied to the 2024 ICD-10 GM codes. It was prepared by comparing the Quan's list of ICD-10 codes with the 2024 German Modification list (2024-GM-ICD-10), removing the codes that were no longer present and, if neccessary, expanding the codes that had been expanded, so that all the subcodes are present in the list.

A table in .md format with all ICD-10 codes is available in the package's root directory.

## License

This project is licensed under the MIT License, a permissive open-source license that allows for reuse, modification, and distribution. Under the MIT License, you are free to use this software in both personal and commercial projects, provided that the original copyright notice and license terms are included in any copies or substantial portions of the software.
The license text is available as a .txt file in the package's root directory.