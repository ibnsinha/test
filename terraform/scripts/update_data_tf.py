# ✅ Generate `data.tf` - Includes Assume Role Policy + Managed Policies

data_tf_content = f"""
# Load Assume Role Policy JSON
data "local_file" "assume_role_policy_json" {{
  filename = "{assume_policy_file}"
}}

# Convert Assume Role Policy JSON to AWS IAM Policy Document
data "aws_iam_policy_document" "instance_assume_role_policy" {{
  json = data.local_file.assume_role_policy_json.content
}}
"""

# ✅ Add Managed Policies to `data.tf`
for policy_arn in managed_policies:
    policy_name = policy_arn.split("/")[-1]  # Extract policy name from ARN
    data_tf_content += f"""
data "aws_iam_policy" "{policy_name}" {{
  arn = "{policy_arn}"
}}
"""

# ✅ Write the final `data.tf` file
with open(f"{module_dir}/data.tf", "w") as f:
    f.write(data_tf_content)

print(f"✅ data.tf created successfully at {module_dir}/data.tf")

