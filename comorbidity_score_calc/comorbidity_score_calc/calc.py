import json
from typing import Union, List
import pkgutil
from pathlib import Path

# Attempt to load the JSON file depending on the environment:
# 1. Use `pkgutil` to load `codes.json` when the package is installed.
# 2. Fallback to loading `codes.json` using `Path` for local development.
# 3. For interactive development, users must manually specify the file path.

# Uncomment the following for installed packages or local development:
# try:
#     data = pkgutil.get_data("comorbidity_score_calc", "codes.json")
#     if data is not None:
#         mappingdata = json.loads(data.decode("utf-8"))
#     else:
#         raise FileNotFoundError
# except (FileNotFoundError, AttributeError):
#     file_path = Path(__file__).parent / "codes.json"
#     with file_path.open("r") as file:
#         mappingdata = json.load(file)

# Uncomment the following for interactive environments (e.g., Jupyter, VSCode):
file_path = '/Users/piotr/Documents/GitHub/cci/comorbidity_score_calc/comorbidity_score_calc/codes.json'
with open(file_path, 'r') as file:
    __mappingdata = json.load(file)

# Fetch the mapping names from the JSON data
# This is later used for checking if the input mapping is one of the available mappings
__mapping_names = list(__mappingdata.keys())


def __check_codes(icd_codes: Union[str, List[str]], code_group: dict, exact_codes: bool) -> bool:
    """
        # A helper function

        Checks if any codes in 'icd_codes' ((the input codes)) correspond to a code in the 'code_group' ((from the list in the script's JSON file)) based on the specified condition.
        There are two possible ways the input codes are processed and checked:
            1. The first way is the more intuitive one and checks for exact matches, i.e. an input code K70.1 will only score if
               there is K70.1 in the selected mapping.
            2. The other way is checking for prefixes. This means that if only K70 is present in the script's library, all its 
               extensions/subcodes will also score, like K70.1, K70.99, etc. This is meant for the situations where additional codes
               are added to the ICD Codes list and coded for a patient but are not yet implemented in this script's library.
               Theoretically, this should not lead to any discrepancies in the final score, as the superior codes are only there in
               the library if all the subcodes are also meant to score.
               For the above reasons this is the default way the script works and if the user

        Parameters
        ----------
        icd_codes : Union[str, List[str]]
            A single ICD code or a list of ICD codes to check for matches.
        code_group : dict
            A dictionary containing a "condition" key (either 'any' or 'both') and a list of 'codes' or 'code groups' to check for matches.
            The structure of 'code_group' is:
                {
                    "condition": "any" | "both",
                    "codes": [list of codes or groups of codes]
                }

        Returns
        -------
        bool:
            True if the condition is met ('any' or 'both'), False otherwise.

        The 'any' condition returns True if any of the codes in 'icd_codes' starts with any, or matches directly, a code from the 'codes' list.
        The 'both' condition returns True only if there is at least one matching prefix, or exact code, in each subgroup of the 'codes' list.
    """

    # Ensure icd_codes is a list
    if isinstance(icd_codes, str):
        icd_codes = [icd_codes]

    # Ensure icd_codes contains codes in upper case:
    icd_codes = [code.upper() for code in icd_codes]

    condition = code_group["condition"]
    codes = code_group["codes"]

    # Now according to the parameter exact_codes, check for either exact codes od prefixes (see explanation in the function's docstring)
    if exact_codes:
        if condition == "any":
            return any(code in icd_codes for code in codes)
            # Explanation of the above logic:
            # The above will return True, if any ICD Code ((variable: code)) from the selected 
            # category in the library ((variable: codes)) is present in the input ICD Codes ((variable: icd_codes))

        elif condition == "both":
            return all(any(code in icd_codes for code in group) for group in codes)
            # Explanation of the above logic:
            # The difference to the previous logic is, that now there are separate groups WITHIN a category of ICD Codes in the library,
            # and we need to check them separately , because only if the codes from BOTH groups are present in the input,
            # will the category score.
            # The any() function: any(code in icd_codes for code in group) is already explained above, 
            # Now this function is used to iterate over all groups of the selected category: (any(...) for group in codes)
            # and returns as many boolean values as there are groups within a category.
            # The outermost function all(...) makes sure the category scores only if all the booleans are True
        return False # If none of the codes was found to match, return False

    else:    
    # The logic in this case is analog to the above with the difference of checking for prefixes with the help of .startswith() method
        if condition == "any":
            # Check if any of the codes in the input icd_codes start with any of the prefixes in codes
            return any(code.startswith(prefix) for code in icd_codes for prefix in codes)
        elif condition == "both":
            # Check if both conditions are met in case of grouped codes
            return all(any(code.startswith(prefix) for code in icd_codes) for group in codes for prefix in group)
        return False

def calculate_score(*, icd_codes: Union[str, list], mapping:str = "cci_icd2024gm", exact_codes:bool = False) -> tuple:
    '''
        Calculates the chosen Comorbidity Score
        For now, only the Charlson Comorbidity Index (Deyo modification) is available.
        The score is calculated based on a given set of ICD codes and a mapping file ('codes.json')

        The score is determined by matching the ICD codes provided to specific categories in a predefined mapping file.
        By default, it calculated the CCI based on the ICD10-2024-GM codes, but alternate mappings (such as Quan's modification) are also available.

        Parameters
        ----------
        icd_codes : Union[str, list]
            A single ICD code or a list of ICD codes that will be evaluated for comorbidities.
        mapping : str, optional
            Identifier for the version of the ICD code mapping to be used. Valid options include:
            - "cci_icd2024gm"         : the 2024 version of the German Modification ICD-10 codes, mapped by the algorithm authors.
            - "cci_icd2024gm_quan"    : a variation based on Quan's implementation, applied to the 2024 ICD-10 GM codes.
            - "cci_icd_quan_orig"     : Quan's mapping, as presented and explained in the following paper , DOI: 10.1097/01.mlr.0000182534.19832.83
        exact_codes : bool, optional
            If True, checks for exact matches between ICD codes and the mapping data. If False, checks for prefix matches. Default is False, meaning
            that if any of the codes in the selected mapping list starts with any of the input codes, it scores

        Returns
        -------
        tuple: (score: int, categories: list)
        - score: An integer representing the total comorbidity score (for CCI it ranges from 0 to 29).
        - categories: A list of categories (comorbidities) that scored based on the input ICD codes.

        Notes
        -----
        - Each category in the CCI has a 'weight' in the mapping file which, contributes to the total score.
        - If multiple comorbidities are present (e.g., neoplasm and metastatic disease), in CCI, only the more severe condition contributes to the score.
        - The 'depends_on' field in the mapping file specifies these hierarchies. For example, if 'dm_simple' depends on 'dm_complicated', 
        the simpler condition will not contribute to the score if the more severe condition is present.
    '''
    
    # Check if the mapping name (input as the "mapping" argument) is available and raise 
    if mapping not in __mapping_names:
        raise ValueError(
            f"Invalid mapping '{mapping}'. Available mappings are: {', '.join(__mapping_names)}"
            )

    # Assuming correct mapping: According to the value of the 'mapping' argument, choose the right mapping
    data = __mappingdata[mapping]

    # Validate input type
    ## The possible input is either a string when only one ICD Code is given or a list of strings when multiple codes are given
    if not isinstance(icd_codes, (str, list)) or (isinstance(icd_codes, list) and not all(isinstance(code, str) for code in icd_codes)):
        raise TypeError(
            "Invalid type for 'icd_codes'. Expected a string or a list of strings."
            )
    
    # Initialize variables for points and categories that scored
    score = 0
    scored_categories = set()

    # Iterate over all the categories to check if any of the codes in a given category is in the input using either the prefix-based matching
    # or exact codes, as according to the exact_codes parameter

    for category, details in data.items():
        for code_group in details["codes"]:
            if __check_codes(icd_codes, code_group, exact_codes = exact_codes):
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

calculate_score(icd_codes = ['K70.11'], mapping = 'cci_icd2024gm', exact_codes=False)