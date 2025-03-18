import boto3
import json
import os
import sys

# Initialize boto3 IAM client
iam_client = boto3.client('iam')

def read_tfvars(file_path):
    """Read terraform.tfvars and extract role_name. Exit if not found."""
    if not os.path.exists(file_path):
        print(f"[ERROR] Required file '{file_path}' not found. Please create it with role_name.")
        sys.exit(1)

    role_name = None
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("role_name"):
                role_name = line.split("=")[1].strip().replace('"', '')
                break

    if not role_name:
        print(f"[ERROR] 'role_name' is missing in {file_path}. It is a mandatory field.")
        sys.exit(1)

    return role_name

def get_role_details(role_name):
    """Fetch IAM Role details"""
    try:
        return iam_client.get_role(RoleName=role_name)['Role']
    except Exception as e:
        print(f"[ERROR] IAM Role '{role_name}' not found: {e}")
        sys.exit(1)

def get_attached_policies(role_name):
    """Fetch Managed Policies attached to an IAM Role"""
    try:
        return iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    except Exception as e:
        print(f"[WARNING] No Managed Policies found for '{role_name}': {e}")
        return []

def get_inline_policies(role_name):
    """Fetch Inline Policies attached to an IAM Role"""
    try:
        return iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
    except Exception as e:
        print(f"[WARNING] No Inline Policies found for '{role_name}': {e}")
        return []

def get_policy_document(policy_arn):
    """Fetch the policy document for a Managed Policy"""
    try:
        policy = iam_client.get_policy(PolicyArn=policy_arn)
        version_id = policy['Policy']['DefaultVersionId']
        policy_version = iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)
        return policy_version['PolicyVersion']['Document']
    except Exception as e:
        print(f"[WARNING] Could not retrieve Managed Policy '{policy_arn}': {e}")
        return None

def get_inline_policy_document(role_name, policy_name):
    """Fetch the policy document for an Inline Policy"""
    try:
        return iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']
    except Exception as e:
        print(f"[WARNING] Could not retrieve Inline Policy '{policy_name}': {e}")
        return None

def get_permissions_boundary(role_name):
    """Fetch the Permissions Boundary if it exists"""
    try:
        role_details = iam_client.get_role(RoleName=role_name)
        return role_details['Role'].get('PermissionsBoundary', {}).get('PermissionsBoundaryArn')
    except Exception as e:
        print(f"[WARNING] No Permissions Boundary found for '{role_name}': {e}")
        return None

def get_instance_profile(role_name):
    """Fetch Instance Profile associated with the IAM Role"""
    try:
        instance_profiles = iam_client.list_instance_profiles_for_role(RoleName=role_name)
        return instance_profiles['InstanceProfiles'][0]['Arn'] if instance_profiles['InstanceProfiles'] else None
    except Exception as e:
        print(f"[WARNING] No Instance Profile found for '{role_name}': {e}")
        return None

def get_role_tags(role_name):
    """Fetch IAM Role Tags"""
    try:
        tags_response = iam_client.list_role_tags(RoleName=role_name)
        return {tag['Key']: tag['Value'] for tag in tags_response.get('Tags', [])}
    except Exception as e:
        print(f"[WARNING] No Tags found for '{role_name}': {e}")
        return {}

def generate_terraform(role_name):
    """Generate Terraform Configuration for the IAM Role dynamically"""
    role = get_role_details(role_name)

    module_dir = "terraform/modules/iam_role/"
    root_tf_file = "terraform/iam_role.tf"
    policies_dir = os.path.join(module_dir, "policies", role_name)
    os.makedirs(policies_dir, exist_ok=True)

    # Generate Assume Role Policy
    assume_policy = role.get('AssumeRolePolicyDocument', {})
    assume_policy_file = f"{policies_dir}/{role_name}_assume_policy.json"
    with open(assume_policy_file, 'w') as f:
        json.dump(assume_policy, f, indent=2)

    # Generate `main.tf` inside `modules/iam_role/`
    main_tf_code = f"""
resource "aws_iam_role" "{role_name}" {{
  name               = "{role_name}"
  assume_role_policy = file("policies/{role_name}_assume_policy.json")
}}
"""

    # Generate `iam_role.tf` at root to call the module
    iam_role_tf_code = f"""
module "iam_role" {{
  source    = "./modules/iam_role"
  role_name = "{role_name}"
}}
"""

    # Save `main.tf` inside module
    with open(f"{module_dir}/main.tf", 'w') as f:
        f.write(main_tf_code)
    print(f"✅ Terraform module saved: {module_dir}/main.tf")

    # Save `iam_role.tf` in the root directory
    with open(root_tf_file, 'w') as f:
        f.write(iam_role_tf_code)
    print(f"✅ Terraform root configuration saved: {root_tf_file}")

if __name__ == "__main__":
    tfvars_path = "terraform/terraform.tfvars"
    role_name = read_tfvars(tfvars_path)
    print(f"✅ Using IAM Role: {role_name}")
    generate_terraform(role_name)

