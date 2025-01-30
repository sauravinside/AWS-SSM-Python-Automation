AWS SSM Automation with Terraform & Python
This project enables automated execution of shell scripts on existing EC2 instances using AWS SSM and Terraform. It ensures that:

✅ Pre-existing EC2 instances get an IAM role with SSM permissions.
✅ SSM Agent is installed on all target instances (supports Amazon Linux, RHEL, Ubuntu, Debian, Windows).
✅ Batch execution of scripts using AWS SSM Run Command.
✅ Works with private instances in the same VPC (via SSM).
🛠️ Project Structure

/ssm-automation/
│── terraform/               # Terraform for SSM role attachment
│   ├── main.tf              # Terraform config (IAM Role & Instance Profile)
│   ├── variables.tf         # Terraform variables
│   ├── terraform.tfvars     # Variable values
│── scripts/                 # Folder to store shell scripts
│   ├── install_grafana.sh   # Example script (replace with any script)
│── config/                  # Configuration files
│   ├── config.json          # Target instances and script details
│── run_script.py            # Python script to install SSM and execute commands
│── requirements.txt         # Required Python packages
│── README.md                # Project documentation
1️⃣ Setup & Prerequisites
🔹 AWS Setup
Ensure you have AWS CLI installed and configured with credentials:

aws configure
Install Terraform (v1.0+):

brew install terraform   # macOS
sudo apt install terraform   # Ubuntu/Debian
Install Python 3.8+ and dependencies:

pip install -r requirements.txt
2️⃣ Configure Terraform
🔹 Update terraform/terraform.tfvars
Modify this file to specify:

AWS region
Existing EC2 instance IDs where SSM should be attached
Example:

aws_region = "us-east-1"
instance_ids = ["i-0abcd1234efgh5678", "i-0123456789abcdef0"]
🔹 Deploy IAM Role & Attach to EC2

cd terraform
terraform init
terraform apply -auto-approve
✅ This attaches the SSM IAM role to existing instances.

3️⃣ Configure Python Script
🔹 Update config/config.json
Modify this file to specify:

Instance IDs where the script should run
Script name (must be inside the scripts/ folder)
Batch size (optional)

{
  "instance_ids": ["i-0abcd1234efgh5678", "i-0123456789abcdef0"],
  "script_name": "install_grafana.sh",
  "batch_size": 5
}
4️⃣ Run the Automation
Run the Python script to:

Ensure SSM Agent is installed
Execute the specified script on target instances

python run_script.py
✅ This will install SSM Agent (if missing) and execute the script via AWS SSM.

5️⃣ Example Script (install_grafana.sh)
Any shell script can be placed in scripts/ and referenced in config.json.
Example scripts/install_grafana.sh:


#!/bin/bash
echo "Installing Grafana..."
sudo apt update -y
sudo apt install -y grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
echo "Grafana installation complete!"
Replace install_grafana.sh with any script of your choice!
6️⃣ How It Works
✅ Step 1: Terraform assigns IAM SSM Role to EC2 instances.
✅ Step 2: Python script checks if SSM Agent is installed (installs if missing).
✅ Step 3: It batches instances and executes the shell script via AWS SSM.
✅ Step 4: Scripts run without SSH access, making it secure and scalable.

7️⃣ Cleanup
To remove IAM Role attachments, run:


cd terraform
terraform destroy -auto-approve
🔹 Future Enhancements
✅ Add support for dynamic inventory with Ansible
✅ Implement error handling & logging
✅ Schedule automatic script execution using AWS Lambda
🚀 Now you can run any script on any EC2 instance automatically! 🚀