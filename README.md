# ARN Messager

ARN Messager is a bot to use in addition of mautrix to allow matrix users without administration right to be connected with a whatsapp group.

## Installation

Create a system user arn-messager
```
useradd --home-dir /opt/arn-messager --system --user-group arn_messager --shell /usr/sbin/nologin
```

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
chown USER:USER /opt/arn-messager/arn-messager.py
chown USER:USER /opt/arn-messager
```

Register a user on a matrix instance and connect with it by running:
```
sudo -u USER ./arn-messager -u @johndoe@domain.tld
```
After giving password (not registered), do CTRL + C to stop arn-messager

Setup a systemd process and start it
```
[Unit]
Description=Le bot ARN-Messager
After=network.target

[Service]
Type=simple
User=arn_messager
Group=arn_messager
WorkingDirectory=/opt/arn-messager/
ExecStart=/opt/arn-messager/venv/bin/python3 /opt/arn-messager/arn-messager.py -vv -u "@arnmessager:sans-nuage.fr"

# Sandboxing options to harden security
# Depending on specificities of your service/app, you may need to tweak these 
# .. but this should be a good baseline
# Details for these options: https://www.freedesktop.org/software/systemd/man/systemd.exec.html
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictNamespaces=yes
RestrictRealtime=yes
DevicePolicy=closed
ProtectSystem=full
ProtectControlGroups=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
LockPersonality=yes
SystemCallFilter=~@clock @debug @module @mount @obsolete @reboot @setuid @swap

# Denying access to capabilities that should not be relevant for webapps
# Doc: https://man7.org/linux/man-pages/man7/capabilities.7.html
CapabilityBoundingSet=~CAP_RAWIO CAP_MKNOD
CapabilityBoundingSet=~CAP_AUDIT_CONTROL CAP_AUDIT_READ CAP_AUDIT_WRITE
CapabilityBoundingSet=~CAP_SYS_BOOT CAP_SYS_TIME CAP_SYS_MODULE CAP_SYS_PACCT
CapabilityBoundingSet=~CAP_LEASE CAP_LINUX_IMMUTABLE CAP_IPC_LOCK
CapabilityBoundingSet=~CAP_BLOCK_SUSPEND CAP_WAKE_ALARM
CapabilityBoundingSet=~CAP_SYS_TTY_CONFIG
CapabilityBoundingSet=~CAP_MAC_ADMIN CAP_MAC_OVERRIDE
CapabilityBoundingSet=~CAP_NET_ADMIN CAP_NET_BROADCAST CAP_NET_RAW
CapabilityBoundingSet=~CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_SYSLOG 

[Install]
WantedBy=multi-user.target
```

If you want you can configure your bot in /opt/arn-messager/johndoe_domain.tld.yml

## Configuration file

Here are the option you can use in YAML file:

 * **user**: The matrix user used by the bot. Example: @johndoe:domain.tld
 * **server**: [Optional] The matrix instance on which the bot will login. Example: matrix.sans-nuage.fr. A default value is deduced from the user param.
 * **device_name**: [Optional] The device name used by this bot to log in. Default is generated randomly.
 * **access_token**: [Optional] To avoid to be prompted for password the first time, you can give an access_token. You can get it with a curl
 * **can_invite_the_bot**: A list of mautrix bots allowed to invite this bot in a room
 * **can_be_invited_by_the_bot**: [Optional] A list of matrix instances from which users are allowed to be invited
 * **can_answer_to_the_bot**: [Optional] Typically whatsapp users allowed to speak to the bot
 * **bot_name**: [Optional] The name of your robot. Default: ARN-messager
 * **im_bridged**: [Optional] A list of social network instant messaging in which this robot could be bridged. Default: Whatsapp
 * **welcome_message**: [Optional] A customize welcome message when the bot join on a room on which it has been invited
 * **lang**: [Optional] The language in which the robot will speak
