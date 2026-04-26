import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()  # loads .env file

# CONFIG
BUCKET_NAME = "vendor-data-24042026"
FOLDER_PATH = "vendor_c_customplatform_data"  # you can change this anytime
BATCH_SIZE = 100
CHECKPOINT_FILE = "uploaded_files.json"

# Dynamically get root folder name
ROOT_FOLDER_NAME = os.path.basename(os.path.abspath(FOLDER_PATH))

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("aws_access_key_id"),
    aws_secret_access_key=os.getenv("aws_secret_access_key"),
    region_name=os.getenv("region_name")
)


def load_uploaded_files():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_uploaded_files(uploaded_files):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(list(uploaded_files), f)


def upload_file(file_path, bucket, key):
    try:
        s3.upload_file(file_path, bucket, key)
        print(f"⬆️  Uploaded: {key}")
        return True
    except ClientError as e:
        print(f"❌ Failed: {file_path} → {e}")
        return False


def get_all_files(folder):
    all_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            full_path = os.path.join(root, file)

            # path inside the given folder
            relative_path = os.path.relpath(full_path, folder)

            # ✅ Add root folder dynamically (vendor_data_a/)
            s3_key = os.path.join(ROOT_FOLDER_NAME, relative_path).replace("\\", "/")

            all_files.append((full_path, s3_key))

    return all_files


def main():
    uploaded_files = load_uploaded_files()
    all_files = get_all_files(FOLDER_PATH)

    remaining_files = [
        (fp, key) for fp, key in all_files if key not in uploaded_files
    ]

    print(f"📁 Root folder: {ROOT_FOLDER_NAME}")
    print(f"📦 Total files: {len(all_files)}")
    print(f"✅ Already uploaded: {len(uploaded_files)}")
    print(f"⏳ Remaining: {len(remaining_files)}")

    for i in range(0, len(remaining_files), BATCH_SIZE):
        batch = remaining_files[i:i + BATCH_SIZE]

        print(f"\n🚀 Batch {i // BATCH_SIZE + 1} ({len(batch)} files)")

        for file_path, key in batch:
            if upload_file(file_path, BUCKET_NAME, key):
                uploaded_files.add(key)

        save_uploaded_files(uploaded_files)

        print(f"✅ Batch done. Total uploaded: {len(uploaded_files)}")

        if i + BATCH_SIZE < len(remaining_files):
            user_input = input("👉 Press ENTER for next batch (or type 'exit'): ")
            if user_input.lower() == "exit":
                print("⏹️ Stopped. Progress saved.")
                break

    print("🎉 Upload complete!")


if __name__ == "__main__":
    main()