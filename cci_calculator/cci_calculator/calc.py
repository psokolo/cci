import json
from typing import Union, List
import pkgutil
from pathlib import Path

try:
    # Try to load with pkgutil (for installed packages)
    data = pkgutil.get_data("cci_calculator", "codes.json")
    if data is not None:
        mappingdata = json.loads(data.decode("utf-8"))
    else:
        raise FileNotFoundError
except (FileNotFoundError, AttributeError):
    # Fall back to local file path with pathlib (for local development)
    file_path = Path(__file__).parent / "codes.json"
    with file_path.open("r") as file:
        mappingdata = json.load(file)


#file_path = 'codes.json'
#with open(file_path, 'r') as file:
#    mappingdata = json.load(file)

def check_codes_exact(icd_codes: Union[str, List[str]], code_group: dict) -> bool:
    """
        Checks if the codes in 'icd_codes' are present in 'code_group' based on the specified condition.
        
        Parameters
        ----------
        icd_codes : Union[str, List[str]]
            A single ICD code or a list of ICD codes to check against the code group.
        code_group : dict
            A dictionary containing a "condition" key (which can be 'any' or 'both') and a list of 'codes' or 'code groups' to check.
            The structure of 'code_group' is:
                {
                    "condition": "any" | "both",
                    "codes": [list of codes or groups of codes]
                }
            
        Returns
        -------
        bool:
            True if the condition is met (either 'any' or 'both'), False otherwise.
        
        The 'any' condition returns True if any code in 'icd_codes' is present in the 'codes' list.
        The 'both' condition returns True only if codes from each subgroup within 'codes' are present in 'icd_codes'.
    """

    # Ensure icd_codes is a list
    if isinstance(icd_codes, str):
        icd_codes = [icd_codes]
        
    condition = code_group["condition"]
    codes = code_group["codes"]
    
    if condition == "any":
        return any(code in icd_codes for code in codes)
    elif condition == "both":
        return all(any(code in icd_codes for code in group) for group in codes)
    return False

def check_codes_startswith(icd_codes: Union[str, List[str]], code_group: dict) -> bool:
    """
        Checks if any codes in 'icd_codes' start with a prefix from the 'code_group' based on the specified condition.

        Parameters
        ----------
        icd_codes : Union[str, List[str]]
            A single ICD code or a list of ICD codes to check for prefix matches.
        code_group : dict
            A dictionary containing a "condition" key (either 'any' or 'both') and a list of 'codes' or 'code groups' to check for prefix matches.
            The structure of 'code_group' is:
                {
                    "condition": "any" | "both",
                    "codes": [list of codes or groups of codes]
                }

        Returns
        -------
        bool:
            True if the condition is met ('any' or 'both'), False otherwise.

        The 'any' condition returns True if any of the codes in 'icd_codes' starts with any prefix from the 'codes' list.
        The 'both' condition returns True only if there is at least one matching prefix in each subgroup of the 'codes' list.
    """

    # Ensure icd_codes is a list
    if isinstance(icd_codes, str):
        icd_codes = [icd_codes]

    condition = code_group["condition"]
    codes = code_group["codes"]

    if condition == "any":
        # Check if any of the codes in icd_codes start with any of the prefixes in codes
        return any(code.startswith(prefix) for code in icd_codes for prefix in codes)
    elif condition == "both":
        # Check if both conditions are met in case of grouped codes
        return all(any(code.startswith(prefix) for code in icd_codes) for group in codes for prefix in group)
    return False

def calculate_score(*, icd_codes: Union[str, list], mapping:str = "icd2024gm", exact_codes:bool = False) -> tuple:
    '''
        Calculates the Charlson comorbidity score (Deyo modification) based on a given set of ICD codes and a mapping file.

        The score is determined by matching the ICD codes provided to specific categories in a predefined mapping file.
        By default, it uses the ICD10-2024-GM codes, but alternate mappings (such as Quan's modification) are also available.

        Parameters
        ----------
        icd_codes : Union[str, list]
            A single ICD code or a list of ICD codes that will be evaluated for comorbidities.
        mapping : str, optional
            Identifier for the version of the ICD code mapping to be used. Valid options include:
            - "icd2024gm"         : the 2024 version of the German Modification ICD-10 codes, mapped by the algorithm authors.
            - "icd2024gm_quan"    : a variation based on Quan's implementation, applied to the 2024 ICD-10 GM codes.
            - "icd2024_quan_orig" : Quan's mapping, as presented and explained in the following paper , DOI: 10.1097/01.mlr.0000182534.19832.83
        exact_codes : bool, optional
            If True, checks for exact matches between ICD codes and the mapping data. If False, checks for prefix matches. Default is False, meaning
            that if any of the codes in the selected mapping list starts with any of the input codes, it scores

        Returns
        -------
        tuple: (score: int, categories: list)
        - score: An integer representing the total Charlson comorbidity score (ranges from 0 to 29).
        - categories: A list of categories (comorbidities) that scored based on the input ICD codes.

        Notes
        -----
        - Each category has a 'weight' in the mapping file which contributes to the total score.
        - If multiple comorbidities are present (e.g., neoplasm and metastatic disease), only the more severe condition contributes to the score.
        - The 'depends_on' field in the mapping file specifies these hierarchies. For example, if 'dm_simple' depends on 'dm_complicated', 
        the simpler condition will not contribute to the score if the more severe condition is present.
    '''
    
    # According to the value of the 'mapping' argument, choose the right mapping
    data = mappingdata[mapping]

    # Validate input type
    ## The possible input is either a string when only one ICD Code is given or a list of strings when multiple codes are given
    if not isinstance(icd_codes, (str, list)) or (isinstance(icd_codes, list) and not all(isinstance(code, str) for code in icd_codes)):
        return None
    
    # Initialize variables for points and categories that scored
    score = 0
    scored_categories = set()

    # Iterate over all the categories to check if any of the codes in a given category is in the input using either the prefix-based matching
    # or exact codes, as according to the exact_codes parameter

    if exact_codes == True:
        for category, details in data.items():
            for code_group in details["codes"]:
                if check_codes_exact(icd_codes, code_group):
                    scored_categories.add(category)
                    break  # Stop checking further groups in this category since it has already scored
    else:
        for category, details in data.items():
            for code_group in details["codes"]:
                if check_codes_startswith(icd_codes, code_group):
                    scored_categories.add(category)
                    break  # Stop checking further groups in this category since it has already scored

    # Handle dependencies and adjust the scored categories accordingly
    ## There are specific hierarchies in the scoring mechanism of this comorbidity index for the case of less and more severe illnesses,
    ## for example: when codes in the input are given for a neoplasm AND a metastatic neoplastic disease, only the latter should score.
    ## The same is true for: complicated Diabetes Mellitus and Diabetes Mellitus without complications; severe liver disease and mild liver disease.
    ## 
    ## This hierarchy is expressed in the JSON file as an element 'depends_on'. If a category has this element, it can only score points,
    ## when the category listed in the 'depends_on' element is not present.
    ## Example: 'dm_simple' has the element 'depends_on' and the dependency is on 'dm_complicated', meaning that 'dm_simple' only scores,
    ## if 'dm_complicated' is not present. 
    ## 
    ## To achieve this, for every category in the set 'scored_categories' the algorithm checks, if this category has an element 'depends_on'
    ## and if that element (the more severe version of the condition) is present in the set, the milder one is removed.    
    for category in list(scored_categories):  # Iterate over a copy of the set to allow modification
        details = data.get(category, {})
        if "depends_on" in details:
            # If the dependency is present in the scored categories, remove this category
            if any(dep in scored_categories for dep in details["depends_on"]):
                scored_categories.remove(category)

    # Calculate the score based on the final adjusted scored_categories
    for category in scored_categories:
        score += data[category]["weight"]

    # Return the score and the list of scored categories
    return score, list(scored_categories)