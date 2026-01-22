import json
import sys

NOTEBOOK_PATH = "main.ipynb"

def refactor_notebook():
    try:
        with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except FileNotFoundError:
        print(f"Error: {NOTEBOOK_PATH} not found.")
        sys.exit(1)

    cells = nb.get('cells', [])
    modified_count = 0

    # 1. Add Import to the first code cell
    for cell in cells:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "import requests" in source and "MarketRegimeModel" not in source:
                print("Adding import to cell...")
                new_source = source.replace(
                    "import requests", 
                    "import requests\nfrom regime_model import MarketRegimeModel"
                )
                cell['source'] = new_source.splitlines(keepends=True)
                modified_count += 1
            break # Only first cell

    # 2. Key Signatures for blocks
    BLOCK_1_SIGNATURE = "gmm = GaussianMixture(n_components=3, random_state=42)"
    BLOCK_2_SIGNATURE = "class HybridBacktester" 
    
    # We look for the GMM logic blocks.
    # Block 1 is the *first* occurrence of GMM logic ~ cell index ~90-100?
    # Block 2 is the *second* occurrence before HybridBacktester.
    
    gmm_blocks_found = 0
    
    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'code':
            source_text = "".join(cell['source'])
            
            # Check for GMM logic
            if BLOCK_1_SIGNATURE in source_text:
                gmm_blocks_found += 1
                print(f"Found GMM block #{gmm_blocks_found} at cell index {i}")
                
                if gmm_blocks_found == 1:
                    # This is likely the "2. REGIME DETECTION" block
                    print("Refactoring Block 1 (Regime Model definition)...")
                    new_source = []
                    # Keep imports or setup if any, but replacing the core logic
                    # We'll just replace the whole cell content for safety/cleanliness 
                    # based on what we saw in the view_file (it was a dedicated cell for regime detection)
                    
                    new_code = [
                        "# ==========================================\n",
                        "# 2. REGIME DETECTION (Refactored)\n",
                        "# ==========================================\n",
                        "model = MarketRegimeModel()\n",
                        "dataset['Regime_Label'] = model.fit_predict(dataset)\n",
                        "print(\"Regime detection completed using MarketRegimeModel.\")\n"
                    ]
                    cell['source'] = new_code
                    modified_count += 1
                    
                elif gmm_blocks_found == 2:
                    # This is likely the redundant block before HybridBacktester
                    # We check if HybridBacktester follows soon, or if this cell *is* it?
                    # The duplicate logic appeared right before HybridBacktester class def.
                    # Actually, we should check if this specific cell contains the duplicate logic.
                    # The duplicate logic was: scaler = ..., gmm = ..., mapping = ...
                    
                    if "class HybridBacktester" not in source_text:
                        print("Refactoring Block 2 (Redundant logic removal)...")
                        new_code = [
                            "# Regime labels already computed in Step 2.\n",
                            "print(\"Using pre-calculated regime labels for Hybrid Strategy.\")\n"
                        ]
                        cell['source'] = new_code
                        modified_count += 1
                    else:
                        print("Skipping Block 2 refactor - mixed content or unsure target.")

    if modified_count > 0:
        with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1) # Formatting might change slightly but that's okay
        print(f"Successfully modified {modified_count} cells.")
    else:
        print("No changes made. Signatures might not have matched.")

if __name__ == "__main__":
    refactor_notebook()
