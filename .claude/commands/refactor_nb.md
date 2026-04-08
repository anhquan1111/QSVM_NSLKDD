You are a Senior Machine Learning Engineer. Your task is to refactor the provided Jupyter Notebook ($ARGUMENTS) into a production-ready Python (.py) module.

STRICT RULES:
1. Extract the core logic into well-structured functions (def) or classes.
2. REMOVE entirely all print(), display(), and visualization/plotting code (e.g., plt.show(), sns.heatmap).
3. NO EXECUTION BLOCKS: Do not include `if __name__ == "__main__":` or any test running code. This file is strictly a module to be imported.
4. Adhere to PEP 8 standards for clean, readable code.
5. LANGUAGE REQUIREMENT: The code is Python, but ALL docstrings, inline comments, and explanatory text MUST be written in VIETNAMESE.

Output ONLY the raw Python code. Do not wrap it in markdown formatting or provide introductory/concluding remarks.