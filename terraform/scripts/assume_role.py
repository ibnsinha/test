import boto3
import json
import os
import sys

def read_tfvars(file_path):
    """Read terraform.tfvars and extract target_account and target_role. Exit if not found."""
    if not os.path.exists(file_path):
        print(f"[ERROR] Required file '{file_path}' not found. Please create it with target_account and target_role.")
        sys.exit(1)

    target_account = None
    target_role = None

    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("target_account"):
                target_account = line.split("=")[1].strip().replace('"', '')
            elif line.startswith("target_role"):
                target_role = line.split("=")[1].strip().replace('"', '')

    if not target_account or not target_role:
        print(f"[ERROR] 'target_account' or 'target_role' is missing in {file_path}. These are mandatory fields.")
        sys.exit(1)

    return target_account, target_role

def assume_role(target_account, target_role):
    """Assume the IAM role in the target AWS account and save credentials securely."""
    sts_client = boto3.client("sts")

    role_arn = f"arn:aws:iam::{target_account}:role/{target_role}"

    try:
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="GitLabAssumeRoleSession"
        )

        credentials = assumed_role["Credentials"]

        # ✅ Save credentials to a temporary secure file (not logged)
        credentials_file = "/tmp/aws_credentials"
        with open(credentials_file, "w") as f:
            f.write(f"AWS_ACCESS_KEY_ID={credentials['AccessKeyId']}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={credentials['SecretAccessKey']}\n")
            f.write(f"AWS_SESSION_TOKEN={credentials['SessionToken']}\n")

        print("✅ Successfully assumed role and saved credentials securely.")

    except Exception as e:
        print(f"[ERROR] Failed to assume role {role_arn}: {e}")
        sys.exit(1)

def main():
    tfvars_path = "terraform/terraform.tfvars"
    
    # Read target account and role from tfvars
    target_account, target_role = read_tfvars(tfvars_path)
    
    # Assume the role and store credentials securely
    assume_role(target_account, target_role)

if __name__ == "__main__":
    main()
