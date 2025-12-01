import os
import glob
from typing import List, Dict

# Mock Storage Configuration
# In a real app, this would be a database or config service
ACCOUNT_REGISTRY = {
    "CHUBBS": {
        "storage_type": "AZURE_BLOB",
        "container": "chubbs-claims",
        "connection_string": "mock_azure_connection_string"
    },
    "AMEX": {
        "storage_type": "LOCAL",
        "root_path": "./mock_cloud/local/Amex"
    },
    "TRAVELERS": {
        "storage_type": "AWS_S3",
        "bucket": "travelers-claims-bucket"
    },
    "DEFAULT": {
        "storage_type": "LOCAL",
        "root_path": "./mock_cloud/local/Default"
    }
}

def search_files(account_name: str, lob: str, policy_id: str, date: str) -> List[Dict[str, str]]:
    """
    Simulates searching for files across different storage backends.
    Returns a list of found files with metadata.
    """
    account_config = ACCOUNT_REGISTRY.get(account_name.upper(), ACCOUNT_REGISTRY["DEFAULT"])
    storage_type = account_config.get("storage_type")
    
    print(f"🔍 Searching in {storage_type} for Account: {account_name}, LoB: {lob}, Policy: {policy_id}, Date: {date}")
    
    found_files = []
    
    # Simulate path construction based on requirements:
    # Path: {root}/{account}/{lob}/{policy_id}/{date}_*.pdf
    
    # For simulation purposes, we will look in a local 'mock_cloud' folder 
    # that represents these different storage locations.
    
    # Normalize date for filename matching (assuming YYYY-MM-DD or similar)
    # If input is DD-MM-YYYY, we might need to be flexible.
    
    base_search_path = os.path.join("mock_cloud", storage_type.lower(), account_name, lob, policy_id)
    
    # Create the directory if it doesn't exist (for simulation so user can see it work)
    if not os.path.exists(base_search_path):
        # We won't create it here during search, but we can log it.
        pass

    # Search pattern
    # We'll look for any PDF in that folder, filtering by date if present in filename
    search_pattern = os.path.join(base_search_path, "*.pdf")
    
    # In a real scenario, we'd use boto3 for S3, azure-storage-blob for Azure, etc.
    # Here we use glob for local simulation of all types.
    
    files = glob.glob(search_pattern)
    
    for f in files:
        # Simple date check in filename
        if date and date in os.path.basename(f):
            found_files.append({
                "filename": os.path.basename(f),
                "path": f,
                "source": storage_type,
                "account": account_name
            })
        elif not date:
             found_files.append({
                "filename": os.path.basename(f),
                "path": f,
                "source": storage_type,
                "account": account_name
            })
            
    return found_files

def create_mock_data():
    """Creates dummy files to simulate the cloud storage."""
    import fpdf
    
    # Data to create
    # Account, LoB, Policy, Date, StorageType
    data = [
        ("CHUBBS", "WC", "2456", "21-09-2024", "AZURE_BLOB"),
        ("AMEX", "AUTO", "1234", "01-01-2024", "LOCAL"),
        ("TRAVELERS", "GL", "9999", "15-05-2024", "AWS_S3")
    ]
    
    for acc, lob, pol, date, stype in data:
        path = os.path.join("mock_cloud", stype.lower(), acc, lob, pol)
        os.makedirs(path, exist_ok=True)
        
        filename = f"{date}_loss_run.pdf"
        full_path = os.path.join(path, filename)
        
        if not os.path.exists(full_path):
            pdf = fpdf.FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Loss Run Report\nAccount: {acc}\nPolicy: {pol}\nDate: {date}", ln=1, align="C")
            pdf.output(full_path)
            print(f"Created mock file: {full_path}")

if __name__ == "__main__":
    create_mock_data()
