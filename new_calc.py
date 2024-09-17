import json
from typing import Union, List

# Load the JSON data and create a dictionary
file_path = 'new_codes.json'
with open(file_path, 'r') as file:
    mappingdata = json.load(file)

def check_codes_exact(icd_codes: Union[str, List[str]], code_group: dict) -> bool:
    """
        Checks if the codes in the 'icd_codes' are present in the 'code_group' according to specific conditions.\n
        The conditions are either 'any' or 'both'. The former means that the function returns True if any of the codes
        in the 'icd_codes' is present in a category. The latter means that the function only returns True, if codes from both subgroups
        of a category are present.
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
        Checks if the codes in 'icd_codes' start with any of the codes in 'code_group'.
        This function returns True if any of the ICD codes in 'icd_codes' start with a code from the 'codes' list in 'code_group'.
        The conditions are either 'any' or 'both'. The former means that the function returns True if any of the codes
        in the 'icd_codes' is present in a category. The latter means that the function only returns True, if codes from both subgroups
        of a category are present.
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

def calculate_score(*, icd_codes: Union[str, list], mapping:str = "icd2024gm", list_cat:bool = False, exact_codes:bool = False) -> Union[int,str]:
    ''' Calculates the charlson comorbidity score (Deyo modification)
        The score is calculated based on the mapping file
        By default it uses the ICD10-2024-GM codes. As of the time of creating the script, the mapping of Quan et al. is also available.
        For information about the mapping check the paper ___ 
    
        Parameters
        ----------
            icd_codes : str|list
                list of the ICD-Codes that should be scored
            mapping : str
                optional: version identifier of the ICD-Code mapping to be used.\n
                          valid options are:\n
                           "icd2024gm"      : the mapping based on the 2024 version of German Modification ICD 10 Codes,
                                              mapped by the authors of the algorithm\n
                           "icd2024gm_quan" : the mapping based on the 2024 version of German Modification ICD 10 Codes,
                                              as implemented by Quan in 2025 (s. paper ___ for more details)
            list_cat : boolean
                if True, prints out a list of categories that scored points. Default is False

        Returns
        -------
        integer: from 0 to 29
        will return none if the input is invalid \n
        list: (optional, if list_cat set to True) a list of categories that scored points 
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

    # Iterate over all the categories to check if any of the codes in a given category is in the input

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

    # Return the total score and, if list_cat was set to True, the list of scored categories
    if list_cat == True:
        print("The categories scored according to the given ICD Codes list are:")
        for x in list(scored_categories):
            print(data[x]['name'])
    return score

calculate_score(icd_codes =["K74.7101"],mapping="icd2024gm", list_cat=True)
calculate_score(["K74.71"],mapping="icd2024gm_quan", list_cat = True)
calculate_score(["K76.7", "I98.2", "K71.2", "K73", "C01", "C80", "B20", "U60.3", "G45.02", "I27.8", "J41.0", "M05.01", "F02.3", "E10.2", "E10.0", "I09.9", "N18.9", "I21.0", "G82.1", "K25.2", "I77.1"], mapping="icd2024gm_quan", list_cat = True)
