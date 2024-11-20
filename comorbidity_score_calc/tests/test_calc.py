import unittest
from comorbidity_score_calc.calc import calculate_score

class TestCalculateScore(unittest.TestCase):
    def test_score(self):
        result = calculate_score(icd_codes="B18.2", mapping="cci_icd2024gm")
        self.assertIsInstance(result, tuple)  # Ensure result is a tuple
        self.assertGreaterEqual(result[0], 0)  # Score should be non-negative


    def test_invalid_mapping(self):
        with self.assertRaises(ValueError):
            calculate_score(icd_codes="B18.2", mapping="invalid_mapping")
    
    def test_invalid_icd(self):
        with self.assertRaises(TypeError):
            calculate_score(icd_codes=123)

    def test_maximal_score(self):
        result = calculate_score(icd_codes = [
            'K70', 'K70.0', 'K70.4', 'I98.2', 'I98.3', 'C77', 'C77.0', 'C00', 'C00.0', 'B20', 'B21',
            'G45', 'G45.0', 'I27.8', 'I27.9', 'M05', 'M05.0', 'F00', 'F00.0', 'I09.9', 'I11.0',
            'I12.0', 'I12.00', 'I21', 'I21.0', 'G04.1', 'G11.4', 'K25', 'K25.0', 'I70', 'I70.0',
            'E10.2', 'E10.20', 'E10.0', 'E10.01', 'B18', 'B18.0', 'I85.0', 'I85.9', 'C77', 
            'C77.0', 'C00', 'C00.0', 'B20', 'B21', 'G45', 'G45.0', 'I27.8', 'I27.9', 'M05', 
            'M05.0', 'F00', 'F00.0', 'I09.9', 'I11.0', 'I12.0', 'I12.00', 'I21', 'I21.0', 
            'G04.1', 'G11.4', 'K25', 'K25.0', 'I70', 'I70.0', 'E10.2', 'E10.20', 'E10.0', 
            'E10.01', 'B18', 'K70.0', 'I85.0', 'I85.9', 'C77', 'C78', 'C00', 'C01', 'B20', 
            'B21', 'G45', 'G46', 'I27.8', 'I27.9', 'M05', 'M06', 'F00', 'F01', 'I09.9', 'I11.0', 
            'I12.0', 'I13.1', 'I21', 'I22', 'G04.1', 'G11.4', 'K25', 'K26', 'I70', 'I71', 
            'E10.2', 'E10.3', 'E10.0', 'E10.1'], mapping = 'cci_icd2024gm')
        self.assertIsInstance(result, tuple)  # Ensure result is a tuple
        self.assertEqual(result[0], 29) # After each category scored at least once, the maximal result should not exceed 29
    
    def test_empty_icd_codes(self):
        """Test that empty ICD codes return a score of 0."""
        result = calculate_score(icd_codes=[])
        self.assertEqual(result, (0, []))  # No codes should result in a score of 0 and no categories scored
    
    def test_nonexistent_code(self):
        result = calculate_score(icd_codes=["ZX99.99"])
        self.assertEqual(result, (0, []))  # Code ZX99.99 should not match any category

    def test_partial_score(self):
        """Test that only matching codes contribute to the score."""
        result = calculate_score(icd_codes=["B18.2", "ZX99.99"], mapping="cci_icd2024gm_quan")
        self.assertEqual(result[0], 1)  # Score should be 1 since B18.2 scores 1
        self.assertIsInstance(result[1], list)  # Ensure categories are returned as a list
    
    def test_dependency_handling(self):
        """Test that dependent categories are handled correctly."""
        # If "dm_simple" depends on "dm_complicated", only the latter should score
        result = calculate_score(
            icd_codes=["E10.0", "E10.2"],  # E10.2 is "dm_complicated" and E10.0 is "dm_simple"
            mapping="cci_icd2024gm"
            )
        self.assertEqual(result[0], 2)
        self.assertNotIn("dm_simple", result[1])  # Ensure the dependent category doesn't score

    def test_mixed_case_icd_codes(self):
        """Test that mixed-case ICD codes are normalized to uppercase."""
        result_upper = calculate_score(icd_codes=["K70"], mapping="cci_icd2024gm")
        result_lower = calculate_score(icd_codes=["k70"], mapping="cci_icd2024gm")
        self.assertEqual(result_upper, result_lower)