#!/usr/bin/env python3

import asyncio
import yaml
import getpass

from nio import AsyncClient, LoginResponse, RoomMessageText, \
    InviteMemberEvent, JoinError, RoomInviteError

CONFIG_FILE = "credentials.yml"
SERVER = "matrix.sans-nuage.fr"
BOT_MATRIX_ID = "@arnmessager:sans-nuage.fr"
DEVICE_NAME = "WPVKCAYZFS"


class Callbacks(object):

    def __init__(self, client, config):
        self.client = client
        self.config = config

    async def invite(self, room, event):
        """Handle an incoming invite event.
        If an invite is received, then join the room specified in the invite.
        """

        # Attempt to join 3 times before giving up
        for attempt in range(3):
            result = await self.client.join(room.room_id)
            if type(result) != JoinError:
                break

            print(f"Error joining room {room.room_id}"
                  f"#{attempt}: {result.message}")

        # Send the welcome message
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": self.config['welcome_message']
            }
        )

    async def message(self, room, event):
        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return

        # Remove start and end spaces from message
        msg = event.body.strip()

        # Ignore non matrix ID message
        for allowed in self.config['matrix_id_allowed']:
            if msg.endswith('@' + allowed):
                break
            if msg.endswith(':' + allowed):
                break
        else:
            return

        # Transform into matrix ID if it's in email format
        if not msg.startswith('@'):
            user_id = "@" + msg.replace('@', ':')

        # Invite the user given
        result = await self.client.room_invite(room.room_id, user_id)
        if type(result) == RoomInviteError:
            await self.client.room_send(
                room.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": result.message
                }
            )
            return
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": f"{user_id} has been invited."
            }
        )

        # Define the user as admin on the matrix miror
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "!wa set-pl " + user_id + " 100"
            }
        )
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "!wa reconnect"
            }
        )
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": f"Ask {user_id} for inviting a new matrix user on the mirrored room."
            }
        )

        # Leave the conversation
        await self.client.room_leave(room.room_id)


async def main() -> None:

    # Open and parse config file
    with open(CONFIG_FILE, "r") as f:
        config = yaml.load(f)
    server = config['server']
    if not (server.startswith("https://") or server.startswith("http://")):
        server = "https://" + server

    # Create a Matrix client thanks to nio lib
    client = AsyncClient(server)
    client.user_id = config['user_id']

    # Listen to message and invitation events
    callbacks = Callbacks(client)
    client.add_event_callback(callbacks.message, (RoomMessageText,))
    client.add_event_callback(callbacks.invite, (InviteMemberEvent,))

    # If no access token, ask password to get one (probably the first connexion)
    access_token = config.get('access_token', None)
    if access_token is None:
        print("No access token stored.")
        print(f"Please enter the password of {client.user_id}.")
        while True:
            pw = getpass.getpass()
            resp = await client.login(pw, device_name=DEVICE_NAME)
            # check that we logged in succesfully
            if isinstance(resp, LoginResponse):
                break
            print(f"server = \"{server}\"; user = \"{client.user_id}\"")
            print(f"Failed to log in: {resp}")

        # Register access token and device id
        config['access_token'] = resp.access_token
        config['device_id'] = resp.access_token
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f)
    else:
        client.access_token = access_token
        client.device_id = config['device_id']

    # Maintain the connexion
    await client.sync_forever(timeout=30000, full_state=True)
    # await client.close()

asyncio.get_event_loop().run_until_complete(main())
