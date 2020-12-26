#!/usr/bin/env python3

import asyncio
import json
import os
import sys
import getpass

from nio import AsyncClient, LoginResponse, RoomMessageText, InviteMemberEvent, JoinError, RoomInviteError

CONFIG_FILE = "credentials.json"

# Check out main() below to see how it's done.


def write_details_to_disk(resp: LoginResponse, homeserver) -> None:
    """Writes the required login details to disk so we can log in later without
    using a password.

    Arguments:
        resp {LoginResponse} -- the successful client login response.
        homeserver -- URL of homeserver, e.g. "https://matrix.example.org"
    """
    # open the config file in write-mode
    with open(CONFIG_FILE, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token  # cryptogr. access token
            },
            f
        )


class Callbacks(object):
    """Collection of all callbacks."""

    def __init__(self, client):
        """Initialize.
        Arguments:
        ---------
            client (nio.AsyncClient): nio client used to interact with matrix
            store (Storage): Bot storage
            config (Config): Bot configuration parameters
        """
        self.client = client

    async def invite(self, room, event):
        """Handle an incoming invite event.
        If an invite is received, then join the room specified in the invite.
        """

        # Attempt to join 3 times before giving up
        for attempt in range(3):
            result = await self.client.join(room.room_id)
            if type(result) == JoinError:
                logger.error(
                    f"Error joining room {room.room_id} (attempt %d): %s",
                    attempt, result.message,
                )
            else:
                break
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "Bonjour, je suis ARN-Messager, un robot qui relaye les messages entre les réseaux de messagerie instantannée WhatsApp et Matrix/Element. Un salon Matrix miroir de ce groupe WhatsApp vient d'être créé. Si vous souhaitez le supprimer, il vous suffit de me retirer des contacts du groupe. Veuillez indiquer dans les 10 minutes l'identifiant sans-nuage.fr pour l'administration du salon miroir. Seuls les comptes @sans-nuage.fr sont autorisés."
            }
        )

    async def message(self, room, event):
        msg = event.body
        print(room.room_id + ":" + msg)
        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return
        if not msg.endswith('@sans-nuage.fr'):
            return
        user_id = "@" + msg.replace('@', ':')
        result = await self.client.room_invite(room.room_id, user_id)
        # Attempt to join 3 times before giving up
        for attempt in range(3):
            if type(result) == RoomInviteError:
                await self.client.room_send(
                    room.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": result.message
                    }
                )
            else:
                print(msg + " has been invited")
                break
        else:
            return
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
        await self.client.room_leave(room.room_id)



async def main() -> None:
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        print("First time use. Did not find credential file. Asking for "
              "homeserver, user, and password to create credential file.")
        homeserver = "https://matrix.sans-nuage.fr"

        if not (homeserver.startswith("https://")
                or homeserver.startswith("http://")):
            homeserver = "https://" + homeserver

        user_id = "@arnmessager:sans-nuage.fr"

        device_name = "WPVKCAYZFS"

        client = AsyncClient(homeserver, user_id)
        pw = getpass.getpass()

        resp = await client.login(pw, device_name=device_name)

        # check that we logged in succesfully
        if (isinstance(resp, LoginResponse)):
            write_details_to_disk(resp, homeserver)
        else:
            print(f"homeserver = \"{homeserver}\"; user = \"{user_id}\"")
            print(f"Failed to log in: {resp}")
            sys.exit(1)

        print(
            "Logged in using a password. Credentials were stored.",
            "Try running the script again to login with credentials."
        )

    # Otherwise the config file exists, so we'll use the stored credentials
    else:
        # open the file in read-only mode
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            client = AsyncClient(config['homeserver'])

            client.access_token = config['access_token']
            client.user_id = config['user_id']
            client.device_id = config['device_id']

        callbacks = Callbacks(client)
        client.add_event_callback(callbacks.message, (RoomMessageText,))
        client.add_event_callback(callbacks.invite, (InviteMemberEvent,))
        print("Logged in using stored credentials. Sent a test message.")

    await client.sync_forever(timeout=30000, full_state=True)
    # Either way we're logged in here, too
    # await client.close()

asyncio.get_event_loop().run_until_complete(main())
