# ARN Messager

ARN Messager is a bot to use in addition of mautrix to allow matrix users without administration right to be connected with a whatsapp group.

## Installation

Clone the repo

```
cd /opt
git clone https://code.ffdn.org/arn/arn-messager
cd arn-messager
```

Create virtual env with dependencies
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Register a user on a matrix instance and connect with it by running:
```
./arn-messager -u @johndoe@domain.tld
```
After giving password (not registered), do CTRL + C to stop arn-messager

Setup a systemd process and start it

If you want you can configure your bot in /opt/arn-messager/johndoe_domain.tld.yml

## Configuration file

Here are the option you can use in YAML file:

 * **user**: The matrix user used by the bot. Example: @johndoe:domain.tld
 * **server**: [Optional] The matrix instance on which the bot will login. Example: matrix.sans-nuage.fr. A default value is deduced from the user param.
 * **device_name**: [Optional] The device name used by this bot to log in. Default is generated randomly.
 * **access_token**: [Optional] To avoid to be prompted for password the first time, you can give an access_token. You can get it with a curl
 * **allowed_users**: A list of mautrix bots allowed to invite this bot in a room
 * **allowed**: [Optional] A list of matrix instances allowed
 * **bot_name**: [Optional] The name of your robot. Default: ARN-messager
 * **im_bridged**: [Optional] A list of social network instant messaging in which this robot could be bridged. Default: Whatsapp
 * **welcome_message**: [Optional] A customize welcome message when the bot join on a room on which it has been invited
 * **lang**: [Optional] The language in which the robot will speak
