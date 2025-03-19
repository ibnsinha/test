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

def get_assume_role_policy(role_name):
    """Fetch Assume Role Policy from AWS IAM"""
    try:
        role_details = iam_client.get_role(RoleName=role_name)
        return role_details['Role']['AssumeRolePolicyDocument']
    except Exception as e:
        print(f"[WARNING] Could not retrieve Assume Role Policy for '{role_name}': {e}")
        return None

def get_attached_policies(role_name):
    """Fetch Managed Policies attached to an IAM Role"""
    try:
        policies = iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        return [policy['PolicyArn'] for policy in policies]
    except Exception as e:
        print(f"[WARNING] No Managed Policies found for '{role_name}': {e}")
        return []

def get_inline_policies(role_name):
    """Fetch Inline Policies attached to an IAM Role"""
    try:
        policies = iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
        return policies
    except Exception as e:
        print(f"[WARNING] No Inline Policies found for '{role_name}': {e}")
        return []

def get_inline_policy_document(role_name, policy_name):
    """Fetch the policy document for an Inline Policy"""
    try:
        return iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)['PolicyDocument']
    except Exception as e:
        print(f"[WARNING] Could not retrieve Inline Policy '{policy_name}': {e}")
        return None

def get_permissions_boundary(role_name):
    """Fetch the Permissions Boundary ARN if set"""
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
        if instance_profiles['InstanceProfiles']:
            return instance_profiles['InstanceProfiles'][0]['InstanceProfileName']
        return None
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
    """Generate Terraform Configuration using locals.tf and data.tf"""
    module_dir = "terraform/modules/iam_role/"
    os.makedirs(module_dir, exist_ok=True)

    # Get Assume Role Policy
    assume_role_policy = get_assume_role_policy(role_name)
    assume_policy_file = f"{module_dir}/policies/{role_name}_assume_policy.json"

    if assume_role_policy:
        with open(assume_policy_file, 'w') as f:
            json.dump(assume_role_policy, f, indent=2)

        assume_policy_tf = f"""
data "aws_iam_policy_document" "instance_assume_role_policy" {{
  json = file("policies/{role_name}_assume_policy.json")
}}
"""
    else:
        assume_policy_tf = "## No Assume Role Policy found for this role"

    # Get Managed Policies
    managed_policies = get_attached_policies(role_name)

    # Generate `locals.tf`
    locals_tf = f"""
locals {{
  iam_role_name               = "{role_name}"
  iam_managed_policy_arns     = {json.dumps(managed_policies, indent=2)}
}}
"""

    # Get Permissions Boundary and Add It If It Exists
    permissions_boundary_arn = get_permissions_boundary(role_name)
    if permissions_boundary_arn:
        locals_tf += f'  iam_permissions_boundary = "{permissions_boundary_arn}"\n'

    with open(f"{module_dir}/locals.tf", 'w') as f:
        f.write(locals_tf)

    # Generate `data.tf`
    data_tf = assume_policy_tf

    for policy_arn in managed_policies:
        policy_name = policy_arn.split("/")[-1]  
        data_tf += f"""
data "aws_iam_policy" "{policy_name}" {{
  arn = "{policy_arn}"
}}
"""

    with open(f"{module_dir}/data.tf", 'w') as f:
        f.write(data_tf)

    # Generate `main.tf`
    main_tf = f"""
resource "aws_iam_role" "{role_name}" {{
  name               = local.iam_role_name
  assume_role_policy = data.aws_iam_policy_document.instance_assume_role_policy.json
  managed_policy_arns = local.iam_managed_policy_arns
"""

    # Attach Permissions Boundary if present
    if permissions_boundary_arn:
        main_tf += f'  permissions_boundary = "{permissions_boundary_arn}"\n'

    main_tf += "  tags = {\n    Name = local.iam_role_name\n  }\n}"

    # Get Instance Profile and Add It Only If It Exists
    instance_profile_name = get_instance_profile(role_name)
    if instance_profile_name:
        main_tf += f"""
resource "aws_iam_instance_profile" "{role_name}" {{
  name = "{instance_profile_name}"
  role = aws_iam_role.{role_name}.name
}}
"""

    with open(f"{module_dir}/main.tf", 'w') as f:
        f.write(main_tf)

    # Generate `iam_role.tf` to call the module
    iam_role_tf = f"""
module "iam_role" {{
  source    = "./modules/iam_role"
  role_name = "{role_name}"
}}
"""
    with open("terraform/iam_role.tf", 'w') as f:
        f.write(iam_role_tf)

if __name__ == "__main__":
    tfvars_path = "terraform/terraform.tfvars"
    role_name = read_tfvars(tfvars_path)
    generate_terraform(role_name)

