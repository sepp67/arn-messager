#!/usr/bin/env python3

import asyncio
import yaml
import getpass
import logging
import argparse
import dns
import dns.resolver
import random
import string

from nio import AsyncClient, LoginResponse, RoomMessageText, \
    InviteMemberEvent, JoinError, RoomInviteError


DEFAULT_CONFIG_PATH = "config.yml"

###############################################################################
# Error management
###############################################################################
logger = logging.getLogger('arn-messager')


class ARNMessagerError(Exception):
    pass

###############################################################################
# Internationalization (i18n)
###############################################################################
TRANSLATIONS = {
    'en_US': {
        'welcome_message': "Hello, I'm {bot_name}, a robot that relays messages between the {im_bridged} and Matrix/Element instant messaging networks. A Matrix lounge mirror of this group has just been created. Please provide a matrix user ID for the administration of the mirror room, this person will be able to add other matrix user to the room. Only {allowed} accounts are allowed as administrator. Example: @johndoe:{example_instance}",
        'invited': "{user} has been invited."
    },
    'fr_FR': {
        'welcome_message': "Bonjour, je suis {bot_name}, un robot qui relaie les messages entre {im_bridged} et le réseau de messagerie instantannée Matrix/Element. Un salon Matrix miroir de ce groupe vient juste d'être créé. Merci d'indiquer l'identifiant matrix de la personne qui administrera ce salon miroir, cette personne pourra ajouter à cette conversation d'autres utilisateurs ou utilisatrices matrix. Seuls les comptes matrix des instances suivantes sont autorisés: {allowed}. Exemple: @johndoe:{example_instance}",
        'invited': "{user} a été invité."
    }
}
EXT_TO_LOCALE = {
    'fr': 'fr_FR',
    'gf': 'fr_FR',
    'corsica': 'fr_FR',
    'bl': 'fr_FR',
    'bzh': 'fr_FR',
    'mq': 'fr_FR',
    'nc': 'fr_FR',
    'pm': 'fr_FR',
    're': 'fr_FR',
    'wf': 'fr_FR',
    'yt': 'fr_FR',
    'alsace': 'fr_FR'
}

def _(id_message, lang=None, **kwargs):
    """ i18n simple function """

    if lang is None:
        lang = _.lang
    if lang in TRANSLATIONS and id_message in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][id_message].format(**kwargs)
    if id_message in TRANSLATIONS["en_US"]:
        return TRANSLATIONS['en_US'][id_message].format(**kwargs)
    return id_message.format(**kwargs)
_.lang = "en_US"


###############################################################################
# Management of events received by the bot
###############################################################################

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
                logger.info(f"Room {room.room_id} joined !")
                break
            logger.error(f"Attempt for joining room {room.room_id}"
                         f"#{attempt}: {result.message}")
        else:
            logger.error(f"Unable to join the room {room.room_id}")

        # Send the welcome message
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": _('welcome_message',
                          bot=config['bot_name'],
                          im_bridged=', '.join(config['im_bridged']),
                          allowed=', '.join(config['allowed']),
                          example_instance=config['allowed'][0])
            }
        )

    async def message(self, room, event):
        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return
        logger.debug("{room.room_id}: {event.body}")
        # Remove start and end spaces from message
        msg = event.body.strip()

        # Ignore non matrix ID message
        for allowed in self.config['allowed']:
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
        logger.info(f"Inviting {user_id} into room {room.room_id}")
        result = await self.client.room_invite(room.room_id, user_id)
        if type(result) == RoomInviteError:
            logger.error(f"Unable to invite {user_id} into {room.room_id}: {result.message}")
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
                "body": _("invited", user=user_id)
            }
        )

        # Define the user as admin on the matrix miror
        logger.error(f"Giving admin priviledge to {user_id} on room {room.room_id}")
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

        # Leave the conversation
        await self.client.room_leave(room.room_id)


###############################################################################
# Configuration management
###############################################################################
def parse_args():
    parser = argparse.ArgumentParser(
    description='Run a bot to use in addition of mautrix to allow matrix users without administration right to be connected with a whatsapp group.',
    epilog="See README.md for more information about installation steps and config file content.")

    parser.add_argument("-u", "--user",
                        help="The matrix user id on which the bot login. Should be something like '@USER:SERVER' .")
    parser.add_argument("-c", "--config",
                        help="Give a specific configuration. By default, ./USER_SERVER.yml is used or config.yml if no user is provided.")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase verbosity")

    args = parser.parse_args()

    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity >= 2:
        logging.basicConfig(level=logging.DEBUG)

    config_path = DEFAULT_CONFIG_PATH
    user = None
    if args.user:
        user = args.user
        config_path = user[1:].replace(':', '_') + '.yml'

    if args.config:
        config_path = args.config
    return config_path, user

def search_matrix_server(user):
    server = user.split(':')[1]
    result = dns.resolver.resolve('_matrix._tcp.' + server, 'SRV')
    if len(result) >= 1:
        server = result[0].target.to_text()
    return server


def load_config(config_path, default_config):
    # Open and parse config file
    try:
        with open(config_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        logger.info(f"No config file found on path {config_path}. Default configuration will be used.")
        pass
    else:
        for key, value in config.items():
            default_config[key] = value

    config = default_config

    if config['user'] is None:
        raise ARNMessagerError("You need to register a specific user on a matrix "
                            "instance and fill the settings 'user' with it or give it in option")
    elif 'server' not in config:
        config['server'] = "https://" + search_matrix_server(config['user'])

    elif not re.match(r'https?://', config['server']):
        config['server'] = "https://" + config['server']

    if 'allowed' not in config:
        config['allowed'] = [config['user'].split(':')[1]]
    return config

async def ask_password(client, config, config_path):
        logger.error("No access token stored.")
        print(f"Please enter the password of {client.user_id}.")
        while True:
            pw = getpass.getpass()
            resp = await client.login(pw, device_name=config['device_name'])
            # check that we logged in succesfully
            if isinstance(resp, LoginResponse):
                break
            print(f"server = \"{config['server']}\"; user = \"{client.user_id}\"")
            print(f"Failed to log in: {resp}")

        # Register access token and device id
        config['access_token'] = resp.access_token
        config['device_id'] = resp.device_id
        with open(config_path, "w") as f:
            yaml.dump(config, f)

async def main() -> None:

    # Initialize default configuration
    config = {
        'bot_name': "ARN-Messager",
        'im_bridged': ["Whatsapp"],
        'welcome_message': 'welcome_message',
        'device_name': ''.join(random.choices(string.ascii_uppercase, k=9)),
        'lang': "en_US"
    }

    # Parse args
    config_path, config['user'] = parse_args()

    # Load configuration
    config = load_config(config_path, config)

    # Configure language used by the bot
    # Use the language associated to the domain extension or switch on en_US if
    # no clue on which language to use
    if 'lang' in config:
        _.lang = config['lang']
    else:
        ext = config['server'].split('.')[-1:][0]
        _.lang = EXT_TO_LANG.get(ext, "en_US")

    # Create a Matrix client thanks to nio lib
    client = AsyncClient(config['server'])
    client.user_id = config['user']

    # Listen to message and invitation events
    callbacks = Callbacks(client, config)
    client.add_event_callback(callbacks.message, (RoomMessageText,))
    client.add_event_callback(callbacks.invite, (InviteMemberEvent,))

    # If no access token, ask password to get one (probably the first
    # connexion)
    access_token = config.get('access_token', None)
    if access_token is None:
        await ask_password(client, config, config_path)
    else:
        client.access_token = access_token
        client.device_id = config['device_id']

    # Maintain the connexion
    logger.info("Running the bot")
    await client.sync_forever(timeout=30000, full_state=True)

asyncio.get_event_loop().run_until_complete(main())
