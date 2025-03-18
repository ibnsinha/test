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

def generate_terraform(role_name):
    """Generate Terraform Configuration using locals.tf and data.tf"""
    module_dir = "terraform/modules/iam_role/"
    policies_dir = os.path.join(module_dir, "policies")
    os.makedirs(policies_dir, exist_ok=True)

    # Get Assume Role Policy
    assume_role_policy = get_assume_role_policy(role_name)
    assume_policy_file = f"{policies_dir}/{role_name}_assume_policy.json"

    if assume_role_policy:
        with open(assume_policy_file, 'w') as f:
            json.dump(assume_role_policy, f, indent=2)

        # Generate `data.tf` dynamically
        data_tf = f"""
data "aws_iam_policy_document" "instance_assume_role_policy" {{
  json = file("policies/{role_name}_assume_policy.json")
}}
"""
    else:
        data_tf = "## No Assume Role Policy found for this role"

    with open(f"{module_dir}/data.tf", 'w') as f:
        f.write(data_tf)
    print(f"✅ Terraform data sources saved: {module_dir}/data.tf")

    # Get Managed Policies
    managed_policies = get_attached_policies(role_name)

    # Generate `locals.tf`
    locals_tf = f"""
locals {{
  iam_instance_profile_name           = "{role_name}"
  iam_instance_profile_managed_policy_arns = {json.dumps(managed_policies, indent=2)}
}}
"""
    with open(f"{module_dir}/locals.tf", 'w') as f:
        f.write(locals_tf)
    print(f"✅ Terraform locals saved: {module_dir}/locals.tf")

    # Generate `main.tf`
    main_tf = f"""
resource "aws_iam_instance_profile" "{role_name}" {{
  name = "${{local.iam_instance_profile_name}}_${{formatdate("YYYY-MM-DD_hh-mm-ss", timestamp())}}"
  role = aws_iam_role.{role_name}.name

  tags = {{
    Name = "${{local.iam_instance_profile_name}}_${{formatdate("YYYY-MM-DD_hh-mm-ss", timestamp())}}"
  }}
}}

resource "aws_iam_role" "{role_name}" {{
  name               = local.iam_instance_profile_name
  assume_role_policy = data.aws_iam_policy_document.instance_assume_role_policy.json
  managed_policy_arns = local.iam_instance_profile_managed_policy_arns

  tags = {{
    Name = "${{local.iam_instance_profile_name}}_${{formatdate("YYYY-MM-DD_hh-mm-ss", timestamp())}}"
  }}
}}
"""
    with open(f"{module_dir}/main.tf", 'w') as f:
        f.write(main_tf)
    print(f"✅ Terraform main configuration saved: {module_dir}/main.tf")

    # Generate `iam_role.tf` to call the module
    iam_role_tf = f"""
module "iam_role" {{
  source    = "./modules/iam_role"
  role_name = "{role_name}"
}}
"""
    with open("terraform/iam_role.tf", 'w') as f:
        f.write(iam_role_tf)
    print(f"✅ Terraform module caller saved: terraform/iam_role.tf")

if __name__ == "__main__":
    tfvars_path = "terraform/terraform.tfvars"
    role_name = read_tfvars(tfvars_path)
    print(f"✅ Using IAM Role: {role_name}")
    generate_terraform(role_name)

