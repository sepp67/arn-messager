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
import re

from time import sleep
from nio import AsyncClient, LoginResponse, RoomMessageText, \
    InviteMemberEvent, JoinError, RoomInviteError


DEFAULT_CONFIG_PATH = "config.yml"
DEFAULT_MAUTRIX_BOT = "@whatsappbot"
DEFAULT_ANSWER_USERS = "@whatsapp_[0-9]+"

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
        'ask_portal_admin': "To add your contact, type '!am' followed by its matrix user ID, e.g. !am @johndoe:{example_instance} . Type help for details",
        'ask_im': """List of commands to bridge your room:
        """,
        'signal_missing_bridge': "Ce salon n'est pas bridgé avec signal. Demandez à votre contact d'inviter : {bot_number}",
        'help': "Hello, I'm {bot}, a robot that enables chating between {im_bridged} and Matrix/Element. A Matrix portal room of this {im_bridged} group has just been created. Please provide a matrix user ID for the administration of the mirror room, this person will be able to add other matrix user to the room. Only {allowed} accounts are allowed as administrator. Example: @johndoe:{example_instance}",
        'invited': "{user} has been invited.",
        'permission_denied': "Only room admins can invite me"
    },
    'fr_FR': {
        'ask_portal_admin': "Pour ajouter votre contact à ce groupe, tapez '!am' suivi de son identifiant Matrix. Exemple: !am @libremax:{example_instance} . Tapez help pour plus d'info",
        'ask_im': """Liste des commandes pour bridger votre salon:
- '!am whatsapp' : Get an invite link for whatsapp user
- '!am whatsapp +33xxxxxxxx' : Invite a whatsapp user
- '!am byebye whatsapp' : Unbridge your room from whatsapp
- '!am signal' : Get an invite link for signal user
- '!am byebye signal'  : Unbridge your room from signal 
""",
        'signal_missing_bridge': "Ce salon n'est pas bridgé avec signal. Demandez à votre contact d'inviter : {bot_number}",
        'help': "Bonjour, je suis {bot}, un robot qui permet de chatter entre {im_bridged} et Element/Matrix. Un salon Matrix miroir de ce groupe vient juste d'être créé. Merci d'indiquer l'identifiant matrix de la personne qui administrera ce salon miroir, cette personne pourra ajouter à cette conversation d'autres utilisateurs ou utilisatrices matrix. Seuls les comptes matrix des instances suivantes sont autorisés: {allowed}. Exemple: @libremax:{example_instance}",
        'invited': "{user} a été invité.",
        'permission_denied': "Seuls les administrateurs de salon peuvent m'inviter"
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

    def __init__(self, client, config, config_path):
        self.client = client
        self.config = config
        self.config_path = config_path

    async def send(self, room, message):
        await self.client.room_send(
            room.room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message
            }
        )


    async def invite(self, room, event):
        """Handle an incoming invite event.
        If an invite is received, then join the room specified in the invite.
        """
        if all([not event.sender.endswith(botuser) for botuser in self.config['botusers']]):
            logger.warning(f"{event.sender} is not an authorized bot user.")
            return

        if event.state_key != self.config['supervisor_botadmin']:
            return

        # Attempt to join 3 times before giving up
        for attempt in range(3):
            result = await self.client.join(room.room_id)
            if type(result) != JoinError:
                logger.info(f"Room {room.room_id} joined !")
                break
            logger.debug(result)
        else:
            logger.error(f"Unable to join the room {room.room_id}")

        # Reconnect to avoid bug
        await self.send(room, f"!wa reconnect")
        sleep(3)

        # 1st approach: the logged in IM account is added to a group
        # bridgebot creates a portal room and invites the logged in Matrix account
        if event.sender in [self.config['whatsapp']['bot'],self.config['signal']['bot']]:
            if event.sender == self.config['whatsapp']['bot']:
                await self.send(room, f"{self.config['whatsapp']['command_prefix']} set-relay")
            else:
                await self.send(room, f"{self.config['signal']['command_prefix']} set-relay")

        
            logger.info(f"{event.sender} set relaybot bridging mode in room {room.room_id}")
            # Send the welcome message for IM-side initialization
            await self.send(room, _('ask_portal_admin',
                    example_instance=self.config['botusers'][0]))
        # 2nd approach: a botusers invites the logged in Matrix account
        # botusers asks user
        else:
            admins = set([user for user, level in room.power_levels.users.items()
                  if level >= 100])
            bots = [self.config['supervisor_botadmin'], self.config['whatsapp']['bot'], self.config['signal']['bot'], '@mautrix_admin:sans-nuage.fr']
            users_sansnuage = [user for user in room.users.keys() 
                    if user.endswith(":sans-nuage.fr") and not (re.match(re.compile(self.config['whatsapp']['puppet']), user) or re.match(re.compile(self.config['signal']['puppet']), user) or user in bots)]
            ## if event.sender in admins:
            if event.sender.endswith(":sans-nuage.fr") and len(users_sansnuage) == 1:
                # Define the user as admin in the matrix portal
                logger.info(f"Ask for {event.sender} on which IM we need to bridge the room {room.room_id}")
                # Ask desired bridging
                await self.send(room, _('ask_im'))
            else:
                logger.info(f"{event.sender} has no admin right so we leave the room {room.room_id}")

                ## await self.send(room, _('permission_denied'))
                await self.send(room, "Seul l'admin du salon est autorisée à lancer des commandes pour bridger le salon, lorsqu'il n'y a pas d'autres membres @sans-nuage.fr")
                # Leave the conversation
                await self.client.room_leave(room.room_id)
                await self.client.room_forget(room.room_id)


    async def message(self, room, event):
        # Ignore messages from ourselves
        if event.sender == self.config['supervisor_botadmin']:
            return
            
        msg = event.body.strip()
        admins = set([user for user, level in room.power_levels.users.items()
                  if level >= 100])

        bots = [self.config['supervisor_botadmin'], self.config['whatsapp']['bot'], self.config['signal']['bot'], '@mautrix_admin:sans-nuage.fr']
        users_sansnuage = [user for user in room.users.keys() 
                if user.endswith(":sans-nuage.fr") and not (re.match(re.compile(self.config['whatsapp']['puppet']), user) or re.match(re.compile(self.config['signal']['puppet']), user) or user in bots)]

        allowed = event.sender.endswith(":sans-nuage.fr") and len(users_sansnuage) == 1
        if any([event.sender.endswith(botuser) for botuser in self.config['botusers']]):

            if msg == "!am whatsapp" and allowed:
                logger.info(f"Start to bridge {room.room_id} with whatsapp")

                # Invite the mautrix_whatsapp bot
                result = await self.client.room_invite(room.room_id, self.config['whatsapp']['bot'])
                sleep(3)
                if type(result) == RoomInviteError:
                    logger.error(f"Unable to invite {self.config['whatsapp']['bot']} into {room.room_id}: {result.message}")
                    await self.send(room, result.message)
                    sleep(3)
                cmd_prefix = self.config['whatsapp']['command_prefix']
                await self.send(room, f"{cmd_prefix} create")
                sleep(3)
                await self.send(room, f"{cmd_prefix} set-relay")
                sleep(5)
                await self.send(room, f"{cmd_prefix} invite-link")
                return

            elif msg == "!am byebye whatsapp" and allowed:
                cmd_prefix = self.config['whatsapp']['command_prefix']
                await self.send(room, f"{cmd_prefix} delete-portal")
                return

            elif msg == "!am signal" and allowed:
                cmd_prefix = self.config['signal']['command_prefix']
                if self.config['signal']['bot'] in admins:
                    await self.send(room, f"{cmd_prefix} invite-link")
                else:
                    await self.send(room, _("signal_missing_bridge", bot_number=self.config['bot_number']))
                return

            elif msg == "!am byebye signal" and allowed:
                cmd_prefix = self.config['signal']['command_prefix']
                await self.send(room, f"{cmd_prefix} unbridge")
                return

            elif msg.startswith("!am whatsapp +") and allowed:
                cmd_prefix = self.config['whatsapp']['command_prefix']
                phone = msg.replace("!am whatsapp +", "")
                await self.send(room, f"{cmd_prefix} pm +" + phone)
                sleep(3)
                result = await self.client.room_invite(room.room_id, self.config['whatsapp']['puppet_prefix'] + phone + ":" + self.config['domain'])
                return

            elif event.sender in self.config['admins'] and (msg.startswith("!wa ") or msg.startswith("!sg ")):
                await self.send(room, msg)

                return


        #logger.debug(f"{room.room_id}#{event.sender}: {event.body}")
        # Remove start and end spaces from message

        # Ignore non matrix ID message
        for allowed in self.config['botusers']:
            allowed = allowed.replace('.', '\.')
            regex = re.compile(f"!am @?[^ ]+[:@]{allowed} *$")
            if regex.match(msg):
                break
        else:
            return

        # Remove the whatsapp username
        user_id = msg.replace("!am ", "").strip()

        # Transform into matrix ID if it's in email format
        if not user_id.startswith('@'):
            user_id = "@" + user_id.replace('@', ':')

        # Deny to invite the bot itself ><
        if user_id == self.config['supervisor_botadmin']:
            return

        # Invite the user given
        logger.info(f"Inviting {user_id} into room {room.room_id}")
        # Not required because the supervisor is now botadmin
        # await self.send(room, f"!wa set-pl {self.config['supervisor_botadmin']} 100")
        # sleep(3)
        result = await self.client.room_invite(room.room_id, user_id)
        if type(result) == RoomInviteError:
            logger.error(f"Unable to invite {user_id} into {room.room_id}: {result.message}")
            await self.send(room, result.message)
            #if not result.message.endswith(' is already in the room.'):
            #    return
        else:
            await self.send(room, _("invited", user=user_id))

            # Define the user as admin in the matrix portal
            logger.info(f"Giving admin right to {user_id} on room {room.room_id}")
            await self.send(room, f"!wa set-pl {user_id} 100")
            #await self.send(room, f"!wa reconnect")




###############################################################################
# Configuration management
###############################################################################
def parse_args():
    parser = argparse.ArgumentParser(
    description='Run a supervisor bot to use in addition of mautrix bridges to allow mautrix bot users to run commands requiring admin rights, e.g. create or delete a portal room.',
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
    try:
        result = dns.resolver.resolve('_matrix._tcp.' + server, 'SRV')
    except:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ['89.234.141.66'] # External resolver
        try:
            result = resolver.resolve('_matrix._tcp.' + server, 'SRV')
        except:
            return server
    if len(result) >= 1:
        server = result[0].target.to_text()[:-1]
    return server


def load_config(config_path, default_config):
    # Open and parse config file
    try:
        with open(config_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        logger.info(f"No config file found on path {config_path}. "
                    "Default configuration will be used.")
        pass
    else:
        for key, value in config.items():
            default_config[key] = value

    config = default_config

    if config['supervisor_botadmin'] is None:
        raise ARNMessagerError("You need to register a specific user on a "
                               "matrix instance and fill the settings "
                               "'supervisor_botadmin' with it or give it in option")
    elif 'server' not in config:
        config['server'] = "https://" + search_matrix_server(config['supervisor_botadmin'])

    elif not re.match(r'https?://', config['server']):
        config['server'] = "https://" + config['server']

    account_server = config['supervisor_botadmin'].split(':')[1]
    if 'botusers' not in config:
        config['botusers'] = [account_server]

    # if 'can_invite_the_bot' not in config:
    #     config['can_invite_the_bot'] = [f"{DEFAULT_MAUTRIX_BOT}:{account_server}"]

    #if 'botpuppets' not in config:
    #    config['botpuppets'] = [f"{DEFAULT_ANSWER_USER}:{account_server}"]

    return config

async def ask_password(client, config, config_path):
        logger.warning("No access token stored.")
        print(f"Please enter the password of {client.user_id}.")
        while True:
            pw = getpass.getpass()
            logger.info('Connecting')
            resp = await client.login(pw, device_name=config['device_name'])
            logger.debug('Connection request received')
            # check that we logged in succesfully
            if isinstance(resp, LoginResponse):
                logger.info('Connection done')
                break
            logger.debug(resp)

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
        'ask_portal_admin': 'ask_portal_admin',
        'device_name': ''.join(random.choices(string.ascii_uppercase, k=9)),
        'lang': "en_US"
    }

    # Parse args
    config_path, config['supervisor_botadmin'] = parse_args()

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
    client.user_id = config['supervisor_botadmin']

    # Listen to message and invitation events
    callbacks = Callbacks(client, config, config_path)
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

    # Set display name
    await client.set_displayname(config['bot_name'])
    
    # Maintain the connexion
    logger.info("Running the bot")
    await client.sync_forever(timeout=30000, full_state=True)

asyncio.get_event_loop().run_until_complete(main())
