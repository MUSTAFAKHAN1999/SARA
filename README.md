To run SARA WEB-UI, you need the following:

• Python v3.8 only

• OpenAI API key

and Provision EC2 instances

1.	Web Server – t2.medium
2.	Bastion – t2.micro
3.	MySQL – t2.medium
4.	Chroma – t3.small (https://docs.trychroma.com/deployment#simple-aws-deployment)


Installation steps (Ubuntu 20.04):

sudo apt update

sudo apt upgrade -y

sudo apt install python3-pip python3-venv

git clone https://github.com/MUSTAFAKHAN1999/SARA.git

In the Config.py file, update your OpenAI API Key, the chroma server IP and the MySQL server String

Finally, run Web interface

flask run app --debug --host=0.0.0.0
