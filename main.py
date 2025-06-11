import os
import time
from etl.extractor import RepositoryData
from uploader.uploader import RepositoryUploader
from dotenv import load_dotenv

load_dotenv() # Loads environment variables at the entry point

# --- Initial Configurations ---
MY_GITHUB_USERNAME = 'FireFox-exe' # Your GitHub username
TARGET_REPO_NAME = 'company-repositories-languages' # Name of the GitHub repository for upload
USERS_TO_PROCESS = ['amzn', 'netflix', 'spotify'] # Companies whose data will be extracted

# --- Welcome and Directory Setup ---
print("\n" + "="*80)
print("               STARTING AUTOMATED GITHUB DATA PIPELINE ")
print("="*80)

# Ensures the 'data' directory exists to save CSVs
if not os.path.exists('data'):
    os.makedirs('data')
    print(" [Main]: 'data/' directory created to store extracted CSV files.")

# --- Upload Process: Repository Preparation ---
print("\n--- STARTING REPOSITORY PREPARATION STEP ON GITHUB ---")
uploader = None # Initialize uploader to None
try:
    uploader = RepositoryUploader(MY_GITHUB_USERNAME)
    uploader.create_repository(TARGET_REPO_NAME)
except ValueError as e:
    print(f" [Main]: FATAL ERROR during Uploader initialization: {e}")
    exit(1) # Exits the program if the token is not configured correctly
except Exception as e:
    print(f" [Main]: UNEXPECTED ERROR initializing Uploader or creating repository: {e}")
    exit(1) # Exits the program in case of a serious error

print("\n---  REPOSITORY PREPARATION STEP FINISHED ---")
time.sleep(1) # Small pause

# --- ETL Process (Extract, Transform, and Local Save) and Upload ---
print("\n---  STARTING ETL AND DATA UPLOAD STEP ---")

for user in USERS_TO_PROCESS:
    print(f"\n--- Processing data for user/organization: '{user}' ---")
    
    # EXTRACTION AND TRANSFORMATION STEP
    try:
        extractor = RepositoryData(user)
        languages_df = extractor.create_languages_df()

        local_file_path = f'data/languages_{user}.csv'
        if not languages_df.empty:
            languages_df.to_csv(local_file_path, index=False)
            print(f"   [Main]: Language data for '{user}' successfully saved locally to: '{local_file_path}'")
            
            # UPLOAD STEP
            if uploader: # Ensure uploader was successfully initialized
                print(f"  [Main]: Starting upload of file '{os.path.basename(local_file_path)}' to GitHub...")
                uploader.upload_file(TARGET_REPO_NAME, os.path.basename(local_file_path), local_file_path)
            else:
                print(f"  [Main]: Uploader not initialized. Skipping upload for '{user}'.")
        else:
            print(f"  [Main]: No repository data found or processed for '{user}'. Will not be saved locally or uploaded to GitHub.")
    except ValueError as e:
        print(f" [Main]: FATAL ERROR processing '{user}': {e}. Please check TOKEN_GITHUB.")
        # Decides whether to continue or exit, here we'll continue for subsequent users
    except Exception as e:
        print(f" [Main]: An unexpected error occurred while processing '{user}': {e}. Skipping to the next user.")

print("\n---  ETL AND DATA UPLOAD STEP FINISHED ---")

print("\n" + "="*80)
print("              DATA PIPELINE COMPLETED (OR TERMINATED)! ")
print("="*80 + "\n")