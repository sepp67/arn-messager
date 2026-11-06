# Plan d'exécution — Lot 2 : refactorisation du fork ARN-Messager

| Champ | Valeur |
|---|---|
| Date de rédaction | 2026-09-28 |
| Dernière mise à jour | 2026-11-06 — clôture documentaire de E0 |
| Statut | Plan validé — **E0 validée**, **E1 non commencée** ; aucun développement engagé |
| Commit analysé | `8705fa8840f2192ff270f795c17da695fd6f1c92` |
| Branche analysée | `lot-2-refactorisation` (identique à `master` et `upstream/master`) |
| Verdict | **GO LOT 2 SOUS CONDITIONS** (voir section 11) |

Toutes les références de lignes `arn-messager.py:NNN` visent le fichier au
commit `8705fa8`, sauf mention explicite de `upstream/testing`.

### Historique des révisions

| Date | Révision | Auteur de la décision |
|---|---|---|
| 2026-09-28 | Rédaction initiale (proposition) | — |
| 2026-11-06 | Synchronisation vérifiée par le propriétaire : `origin/lot-2-refactorisation` = HEAD = `8705fa8`, aucun commit distant en avance | Propriétaire |
| 2026-11-06 | Clôture de E0 : arbitrages A-01 à A-08 validés (§10.1), orientations P1 à P5 acceptées (§10.3), codes de sortie 0/1/2/3 confirmés (§10.4), contrat runtime à harmoniser avant E6, faux objets `matrix-nio` reportés de E1 à E3 | Propriétaire |

Les recommandations d'origine sont conservées dans les tableaux pour la
traçabilité ; la colonne « État » ou la mention « Décision » indique ce qui a
été validé.

---

## 1. Objet et périmètre

### 1.1 Objectif du Lot 2

Remettre en état le fork d'ARN-Messager pour qu'il puisse recevoir, au Lot 3,
le parcours de revendication par identifiant et code, **sans implémenter ce
parcours**. Concrètement, à la sortie du Lot 2 :

- le comportement historique utile est figé par des tests de caractérisation,
  puis préservé (ou modifié intentionnellement et explicitement) par la
  refactorisation ;
- le code ne contient plus aucune valeur propre à l'installation d'origine
  (`sans-nuage.fr`, résolveur DNS, préfixes `!wa`/`!sg` en dur) ;
- les MXID et domaines sont analysés structurellement, jamais par suffixe ;
- la configuration suit le schéma du contrat runtime et échoue explicitement
  si elle est invalide ;
- la session Matrix est gérée de façon non interactive, hors du fichier de
  configuration, conformément à RT-AM-020/022/044 ;
- aucun secret n'est journalisé ;
- le code asynchrone ne contient plus d'attente bloquante ;
- la logique de décision est testable sans client Matrix.

### 1.2 Éléments inclus

- Suppression des valeurs codées en dur (domaines, MXID, résolveur DNS,
  préfixes de commande des bridges).
- Analyse et validation des identifiants Matrix (MXID, nom de serveur).
- Nouveau chargement de configuration strict, aligné sur le contrat runtime
  (§12 du contrat), y compris la lecture des secrets par fichiers montés.
- Journalisation sans secrets (filtre de rédaction, suppression des
  journalisations brutes).
- Remplacement des 7 appels `time.sleep()` par des attentes asynchrones.
- Séparation décision / exécution : fonctions pures de décision, adaptateur
  Matrix mince, constructeur de commandes Mautrix.
- Gestion de session : `SessionStore` dans `/data/session/`, login par
  fichier de mot de passe, réauthentification unique, codes de sortie.
- Démarrage propre : `asyncio.run`, arrêt sur `SIGTERM`, non-rejeu des
  événements antérieurs au démarrage.
- Gestion d'erreurs des appels Matrix existants.
- Refus explicite des salons chiffrés (décision PF-AM-011).
- Mise à jour et épinglage des dépendances, retrait du support E2EE.
- Tests de caractérisation, unitaires, asynchrones, de configuration et de
  non-divulgation ; CI minimale.
- Documentation technique de la configuration et de la session.

### 1.3 Éléments explicitement exclus

| Exclu | Lot |
|---|---|
| Commandes `!am code`, `!am codes`, `!am revoke`, `!am admin`, saisie `<identifiant> <code>` | 3 |
| Antichambres (`matrix_lobbies`), création/reconnaissance, PF-AM-013 | 3 |
| Machine à états des autorisations et des salons-portails | 3 |
| Génération d'identifiants/codes, hachage, trois tentatives, verrouillages | 3 |
| TTL, expiration et fermeture autonome des portails | 3 |
| Passage du niveau de pouvoir du propriétaire de 100 à 50 | 3 |
| Dépendance et accès PostgreSQL, migrations | 3 (migrations livrées au Lot 3/4) |
| `Dockerfile`, utilisateur non root, healthcheck, publication d'image | 4 |
| `tasks/arn_messager.yml`, templates, Vault, intégration dans le rôle | 5 |
| Pilote | 6 |
| Support E2EE (store Olm, appareils, clés) | Hors POC (PF-AM-011) |

Le Lot 2 peut **préparer une interface** pour ces éléments (par exemple
valider syntaxiquement les sections `claims`, `power_levels` et `postgresql`
de la configuration), mais n'en implémente aucun comportement.

### 1.4 Documents de référence

| Document | Emplacement | Rôle |
|---|---|---|
| Cahier des charges | `../cahier-des-charges-arn-messager.md` | Référence fonctionnelle normative (cité « cdc §N ») |
| Contrat runtime (v4, fichier nommé v3) | `../CONTRACT-ARN-MESSAGER-RUNTIME-ANSIBLE-v3.md` | Interface image ↔ Ansible (cité « RT-AM-NNN ») |
| Préflight croisé (v4, fichier nommé v3) | `../PREFLIGHT-CROISE-ARN-MESSAGER-ANSIBLE-v3.md` | Audit à vérifier (cité « PF-AM-NNN ») |

Les trois documents ont été lus intégralement. Ils ne sont pas modifiés par
cette intervention.

---

## 2. État Git et état initial du dépôt

### 2.1 Commit, branche, working tree

| Élément | Constat |
|---|---|
| Chemin | `~/Documents/repos/2-projet-matrix-stack/5-arn-messager` (conforme) |
| Commit courant | `8705fa8840f2192ff270f795c17da695fd6f1c92` — « make arn bot admin in the room (again) not sure it's needed » (2024-10-24) |
| Correspondance avec la référence `8705fa8` | **Exacte** (HEAD = référence) |
| Branche courante | `lot-2-refactorisation` — **déjà créée et déjà publiée** sur `origin` (`origin/lot-2-refactorisation` = `8705fa8`) |
| Autres branches locales | `master` (= `8705fa8`) |
| Working tree | Propre avant cette intervention (aucune modification, aucun fichier non suivi) |
| Historique | Présent, 35 commits sur `master` — résout PF-AM-001 côté bot |

### 2.2 Remotes

| Remote | URL | Branches |
|---|---|---|
| `origin` | `git@github.com:sepp67/arn-messager.git` | `master`, `lot-2-refactorisation` |
| `upstream` | `https://code.ffdn.org/arn/arn-messager.git` | `master` (= `8705fa8`), `testing`, `telegram` |

Aucun identifiant n'apparaît dans les URL.

### 2.3 Branches amont non intégrées — constat majeur

`upstream/testing` contient **31 commits absents de `master`**, du
2024-02-26 au **2026-01-28** (auteurs « gaut », « ljf », « Gredin 67 »).
Leur diff par rapport à `8705fa8` touche 425 lignes de `arn-messager.py`.
Ces commits apportent notamment :

- `a01ae4a` « rework and remove sans-nuage » ;
- un renommage des clés de configuration (`supervisor_botadmin` →
  `relaybot_admin`, `botusers` → `bot_users`, `server` → `public_baseurl`) ;
- `bffb302` « get botpassword from config at first start » (mot de passe en
  clair dans le fichier de configuration) ;
- `9f28b5b` « matrix modo level 50 » (seuil `> 49` pour les modérateurs, mais
  la promotion reste à 100) ;
- `cc2593c` « bump matrix-nio 25.2 » et retrait de `[e2e]` des dépendances
  de base ;
- de nouvelles commandes Mautrix (`create-group`, `sync-portal`,
  `sync group`, `join <lien>`) et un regex de puppet
  `@whatsapp_lid-[0-9]+`, qui suggèrent un alignement sur les bridges
  Mautrix « bridgev2 » récents ;
- mais aussi une régression de sécurité : `logger.debug(f"{room.room_id}#{event.sender}: {event.body}")`
  est réactivé (`upstream/testing:arn-messager.py:362`) et journaliserait les
  codes secrets au Lot 3.

`upstream/telegram` diverge également (ajout Telegram, 104 lignes).

Le préflight et le contrat ont été établis sur `master`. Le choix de la base
du fork est traité au point **A-01** (section 10) : il conditionne les tests
de caractérisation.

### 2.4 Fichiers suivis

```text
.gitignore                    3 lignes
LICENSE                       AGPLv3
README.md                     98 lignes — installation systemd, interactive
arn-messager.py               462 lignes — unique fichier source
arn-messager_domain.tld.yml   0 octet — exemple de configuration VIDE
requirements.txt              5 lignes
```

Il y a un seul module Python, sans package, et le nom de fichier contient un
tiret, donc il n'est pas importable par `import`.

### 2.5 Dépendances

| Dépendance | Version déclarée | Observation |
|---|---|---|
| `wheel` | non épinglée | Inutile à l'exécution |
| `PyYAML` | `==6.0` | 6.0 a des problèmes connus de construction avec Cython 3 / Python ≥ 3.12 ; 6.0.1+ requis |
| `python-olm` | non épinglée | Nécessite `libolm` (déprécié en amont) ; utile seulement pour E2EE, hors POC |
| `matrix-nio[e2e]` | `==0.20.1` | 2022 ; dernière version publiée : 0.26.0 ; `upstream/testing` utilise 0.25.2 |
| `dnspython` | `==2.3.0` | Utilisé seulement pour la découverte SRV à supprimer (L2-AM-006) |

Il n'y a ni `pyproject.toml`, ni fichier de verrouillage, ni dépendances de
développement, ni version de Python déclarée. L'environnement local dispose
de Python 3.10.12, sans `matrix-nio` installé.

### 2.6 Tests et automatisations

| Élément | Présent |
|---|---|
| Tests | Non |
| CI (`.github/`, `.gitlab-ci.yml`, `.woodpecker*`) | Non |
| `Dockerfile` | Non |
| Documentation technique | Non (seulement le `README.md`, obsolète) |
| Linter/formatter configuré | Non |

`.gitignore` contient `*.yml`, ce qui ignorerait les futurs workflows CI, le
fichier Compose et les exemples de configuration (L2-AM-002).

---

## 3. Architecture actuelle du bot

### 3.1 Point d'entrée

`arn-messager.py:462` exécute `asyncio.get_event_loop().run_until_complete(main())`
**au niveau module**, sans garde `if __name__ == "__main__"`. Importer le
fichier lance le bot. `get_event_loop()` hors boucle est déprécié depuis
Python 3.10 et échoue sur les versions récentes.

`main()` (`:411-460`) enchaîne : configuration par défaut → `parse_args()` →
`load_config()` → langue → `AsyncClient` → enregistrement des callbacks →
login ou token → `set_displayname` → `sync_forever(timeout=30000, full_state=True)`.

### 3.2 Chargement de la configuration

- `parse_args()` (`:309-336`) : `-u` fournit le MXID et dérive le chemin
  `USER_SERVER.yml` ; `-c` force le chemin ; `-v`/`-vv` configure le logging
  racine (sinon aucun `basicConfig`).
- `load_config()` (`:354-389`) : lit le YAML avec `yaml.FullLoader`, fusionne
  dans un dictionnaire par défaut. Un fichier absent est ignoré silencieusement.
  La seule validation porte sur `supervisor_botadmin`. `server` est déduit par
  une résolution DNS SRV (`search_matrix_server`, `:338-351`). `botusers` vaut
  par défaut le domaine du bot.
- Clés effectivement lues ailleurs sans validation : `botusers`,
  `supervisor_botadmin`, `whatsapp.{bot,command_prefix,puppet}`,
  `signal.{bot,command_prefix,puppet}`, `admins`, `bot_number`,
  `device_name`, `bot_name`, `lang`, `access_token`, `device_id`.

### 3.3 Authentification Matrix

- Si `access_token` est présent dans la configuration, il est injecté
  directement (`:448-453`), sans vérification (pas de `whoami`).
- Sinon, `ask_password()` (`:391-409`) demande le mot de passe par `getpass`,
  **en boucle infinie** jusqu'au succès, puis **réécrit tout le fichier de
  configuration** (`yaml.dump(config)`), `access_token` et `device_id`
  compris, avec les permissions par défaut.
- Il n'y a aucune gestion d'un token révoqué en cours de fonctionnement.

### 3.4 Traitement des événements

`Callbacks` (`:97-301`) enregistre deux callbacks :

- `invite(room, event)` sur `InviteMemberEvent` (`:115-175`) : filtre
  l'expéditeur par suffixe de domaine, rejoint le salon (3 essais), envoie
  `!wa reconnect`, puis :
  - si l'invitation vient d'un bot de bridge : `set-relay` et message
    `ask_portal_admin` (création côté WhatsApp/Signal) ;
  - sinon, si l'invitant est l'unique humain `:sans-nuage.fr` : liste des
    commandes (`ask_im`) ;
  - sinon : message en français codé en dur, puis départ et oubli du salon.
- `message(room, event)` sur `RoomMessageText` (`:178-300`) :
  - commandes réservées à un expéditeur d'un domaine `botusers` et « seul
    humain sans-nuage du salon » : `!am reset`, `!am whatsapp`,
    `!am ciao whatsapp`, `!am ping whatsapp`, `!am signal`,
    `!am unbridge signal`, `!am ciao signal`, `!am sync signal` ;
  - relais de toute commande `!wa …`/`!sg …` pour les `admins` ;
  - puis, **pour tout expéditeur** (puppet WhatsApp compris),
    `!am <mxid>` : invitation du MXID et promotion à 100 via le bridge.

### 3.5 Parsing des commandes

Il est fait par comparaison exacte de chaînes (`msg == "!am whatsapp"`) dans
une longue chaîne `if/elif`, et par une regex construite à chaud pour
`!am <mxid>` (`:262-268`), puis par des `str.replace` (`:271-275`). Aucune
fonction de parsing n'est isolée.

### 3.6 Interactions Matrix et Mautrix

| Appel | Lignes |
|---|---|
| `client.join` | `:128` |
| `client.room_send` (via `send`) | `:104-112` |
| `client.room_invite` | `:205`, `:286` |
| `client.room_leave` / `room_forget` | `:174-175` |
| `client.login`, `set_displayname`, `sync_forever` | `:397`, `:456`, `:460` |

Commandes Mautrix envoyées sous forme de messages texte :

| Commande | Préfixe | Lignes | Déclencheur |
|---|---|---|---|
| `reconnect` | `!wa` codé en dur | `:137` | Toute invitation acceptée, même Signal |
| `set-relay` | config | `:144`, `:146`, `:196`, `:215` | Invitation par un bot, `!am reset`, `!am whatsapp` |
| `create` | config | `:213` | `!am whatsapp` |
| `invite-link` | config | `:217`, `:233` | `!am whatsapp`, `!am signal` |
| `delete-portal` | config | `:222`, `:245` | `!am ciao …` |
| `ping` | config | `:227` | `!am ping whatsapp` |
| `unbridge` | config | `:240` | `!am unbridge signal` |
| `sync` | config | `:250` | `!am sync signal` |
| `set-pl <bot> 100` | `!wa` codé en dur | `:284` | `!am <mxid>` |
| `set-pl <user> 100` | `!wa` **et** `!sg` codés en dur | `:299-300` | `!am <mxid>` réussi |
| Relais brut `!wa …`/`!sg …` | — | `:253-255` | Membre de `admins` |

### 3.7 Persistance actuelle

Il n'y a aucune base de données. La seule persistance est le fichier de
configuration YAML, réécrit par le bot avec le token d'accès. L'état des
salons est lu depuis le cache de `matrix-nio` (`room.users`,
`room.power_levels`). Le jeton de synchronisation (`next_batch`) n'est pas
persisté.

### 3.8 Principaux couplages

1. `Callbacks.message` mêle parsing, autorisation (analyse des membres et
   niveaux), chaînes Mautrix, appels réseau, temporisations et messages i18n.
2. Le bloc de calcul `bots`/`users_sansnuage` est dupliqué (`:156-160` et
   `:184-189`), avec les mêmes valeurs en dur.
3. L'état global mutable `_.lang` (attribut de fonction) est utilisé par l'i18n.
4. La configuration est un `dict` libre, partagé et muté par `ask_password`.
5. Le démarrage est effectué à l'import (non testable).

---

## 4. Constats vérifiés

Légende des priorités : **P0** bloque la testabilité ou la sécurité ;
**P1** est une exigence explicite du cdc ou du contrat ; **P2** relève de la
robustesse ou de la maintenabilité ; **P3** est mineur.

Légende de vérification : **CONF** = constat du préflight confirmé ;
**INF** = infirmé ou corrigé ; **NEW** = nouveau constat ; **INT** = nécessite
un test d'intégration.

### 4.1 Tableau des constats

| ID | Priorité | Fichier ou composant | Constat vérifié | Exigence liée | Traitement proposé | Lot |
|---|---|---|---|---|---|---|
| L2-AM-001 | P0 | Dépôt / branches | **NEW** — `master` (`8705fa8`, 2024-10) a 31 commits de retard sur `upstream/testing` (2026-01), qui refond le même fichier | cdc §2.2 ; PF-AM-001 | Base arbitrée : `8705fa8`, sans fusion de `upstream/testing` (A-01, validé le 2026-11-06) | 2 (E0) |
| L2-AM-002 | P1 | `.gitignore:2` | **NEW** — `*.yml` ignore tous les YAML ; l'exemple suivi `arn-messager_domain.tld.yml` est vide (0 octet) | cdc §11 (pipeline), §13 (tests) | Remplacer par des exclusions ciblées (`/config.yml`, `/*_*.yml` locaux, `venv/`, `__pycache__/`, `.pytest_cache/`) ; supprimer l'exemple vide au profit de `config.example.yml` | 2 |
| L2-AM-003 | P0 | `arn-messager.py:462` | **NEW** — exécution à l'import, nom de fichier non importable, `get_event_loop()` déprécié | cdc §13 (tests) | Garde `__main__` immédiate, puis package importable et `asyncio.run` | 2 |
| L2-AM-004 | P1 | `Callbacks.invite:158`, `Callbacks.message:187` | **CONF** — MXID `@mautrix_admin:sans-nuage.fr` codé en dur | cdc §13 ; PF-AM §2 | Remplacer par `matrix.technical_accounts` | 2 |
| L2-AM-005 | P1 | `Callbacks.invite:159-162,171`, `Callbacks.message:188-191` | **CONF** — domaine `:sans-nuage.fr` codé en dur (filtre et message FR) | cdc §13 | Remplacer par `matrix.allowed_domains` et un message i18n | 2 |
| L2-AM-006 | P1 | `search_matrix_server:338-351`, `load_config:373-377` | **NEW** — résolveur DNS externe codé en dur `89.234.141.66`, découverte par SRV `_matrix._tcp` (qui désigne la fédération, pas l'API client), `except:` nus, appel DNS bloquant dans `main()` | cdc §12.1 ; RT-AM-041 (`homeserver_url` explicite) | Supprimer la découverte ; `matrix.homeserver_url` obligatoire ; retirer `dnspython` | 2 |
| L2-AM-007 | P1 | `invite:137`, `message:284,299,300` | **NEW** — préfixes `!wa`/`!sg` codés en dur malgré `command_prefix` ; `!wa reconnect` envoyé aussi dans les salons Signal | cdc §12.1 (`command_prefix` par réseau) | Constructeur de commandes par réseau (`networks.*.command_prefix`) | 2 |
| L2-AM-008 | P0 | `invite:119`, `message:192` | **CONF** — autorisation par `event.sender.endswith(botuser)` : `@x:evilsans-nuage.fr` passe si `botusers = ["sans-nuage.fr"]` | cdc §13 (« parser les MXID ») | `parse_mxid()` puis comparaison exacte du nom de serveur à `allowed_domains` | 2 |
| L2-AM-009 | P1 | `message:262-275` | **CONF + NEW** — regex `!am @?[^ ]+[:@]{domaine} *$` : seuls les points sont échappés ; `[^ ]+` accepte `:` (`@a:b:domaine`) ; `replace("!am ", "")` remplace toutes les occurrences ; conversion « e-mail » qui remplace tous les `@` | cdc §13 | Fonction `parse_mxid()` conforme à la grammaire Matrix, avec `re.escape` et un parsing en jetons ; forme `user@domaine` conservée avec parsing strict (A-05) | 2 |
| L2-AM-010 | P2 | `load_config:379`, `search_matrix_server:339` | **NEW** — `split(':')[1]` : un nom de serveur avec port (`@bot:hote:8448`) donne `hote` | cdc §13 | Découpage sur le premier `:` via `parse_mxid()` | 2 |
| L2-AM-011 | P2 | `invite:160`, `message:189` | **NEW + INT** — `re.match(puppet)` non ancré en fin, recompilé à chaque utilisateur et à chaque message ; clé `puppet` au lieu de `puppet_regex` ; motif historique `@whatsapp_[0-9]+` probablement obsolète (bridgev2 : `@whatsapp_lid-…`, cf. `upstream/testing`) | cdc §12.1 ; RT-AM-052 ; PF-AM-007 | Compiler une fois au chargement avec `re.fullmatch` ; valeur réelle validée au Lot 3 | 2 (mécanisme) / 3 (valeur) |
| L2-AM-012 | P1 | `invite:138,173`, `message:206,212,214,216,285` | **CONF, compte corrigé** — **7** appels `time.sleep()` (le préflight en annonçait 4), jusqu'à 16 s de blocage de la boucle pour `!am whatsapp` | cdc §13 ; PF-AM-008 | Attentes `asyncio.sleep` exécutées par l'adaptateur ; délais en constantes nommées | 2 |
| L2-AM-013 | P2 | `nio.AsyncClient.sync_forever` | **NEW + INT** — `matrix-nio` attend les callbacks séquentiellement pendant la synchronisation : même avec `asyncio.sleep`, un traitement long retarde les suivants | cdc §13 | Documenter ; ne pas paralléliser au Lot 2 ; remplacer les délais fixes par l'attente des réponses du bot de bridge au Lot 3 si PF-AM-007 le permet | 2 (doc) / 3 |
| L2-AM-014 | P1 | `load_config:354-389` | **CONF** — seule `supervisor_botadmin` est validée ; `KeyError` différés (`whatsapp`, `signal`, `admins`, `bot_number`) ; fichier absent ignoré ; fichier vide → `AttributeError` ; `FullLoader` ; clés inconnues acceptées | cdc §13 ; RT-AM-018/019 | Chargeur strict (`yaml.safe_load`, dataclasses figées, erreurs agrégées, sortie non nulle) | 2 |
| L2-AM-015 | P1 | Schéma de configuration | **NEW** — le schéma actuel (`supervisor_botadmin`, `server`, `botusers`, `bot_number`, `whatsapp.puppet`…) diffère du schéma du contrat §12 (`matrix.*`, `secrets.*`, `networks.*`, `claims.*`, `power_levels.*`, `postgresql.*`) ; `bot_name`, `lang`, `device_name` n'existent pas dans le contrat | RT-AM-014/015/017 | Adopter le schéma du contrat ; clés supplémentaires regroupées dans une section optionnelle `bot.*` (A-04) ; sections `claims`, `power_levels`, `postgresql` validées mais inutilisées | 2 |
| L2-AM-016 | P0 | `ask_password:405-409` | **NEW** — le bot réécrit tout le fichier de configuration avec `access_token` et `device_id` en clair, sans écriture atomique ni permissions restreintes | RT-AM-022/024 ; PF-AM-010 (config immuable, session 0600 dans `/data/session/`) | `SessionStore` dédié : écriture atomique (fichier temporaire + `os.replace`), 0600/0700 ; configuration jamais écrite | 2 |
| L2-AM-017 | P1 | `ask_password:391-403` | **CONF** — login interactif `getpass`, boucle infinie sans délai en cas d'échec | cdc §10, §11 ; RT-AM-020/044 | Login non interactif depuis `secrets.matrix_password_file`, une tentative, code de sortie non nul | 2 |
| L2-AM-018 | P1 | `ask_password:403` | **INF partiel** — `logger.debug(resp)` n'est atteint que si `resp` n'est **pas** un `LoginResponse` (donc `LoginError`, sans token) ; le risque d'écrire un token dans les journaux ne vient pas de là mais du fichier de configuration (L2-AM-016) et du niveau DEBUG global (L2-AM-027) | cdc §13 ; RT-AM-025/066 ; PF-AM-009 | Supprimer quand même la journalisation d'objets bruts ; ne journaliser que `status_code`/`errcode` | 2 |
| L2-AM-019 | P1 | `message:258` (commenté) et `upstream/testing:362` | **NEW** — la journalisation de `event.body` est commentée sur `master` mais réactivée sur `testing` ; au Lot 3 elle exposerait les codes secrets | cdc §5.3 (« ne journalise jamais un code secret complet ») ; RT-AM-067 | Interdire la journalisation du corps des messages ; test de non-divulgation | 2 |
| L2-AM-020 | P1 | `invite:127-134`, `message:205-213`, `send:104-112`, `main:456,460` | **INF partiel + NEW** — le préflight ne cite que `RoomInviteError:287` ; en réalité, trois cas sont gérés (`JoinError:129`, `RoomInviteError:208`, `:287`), mais : après un échec de `join`, le code continue d'envoyer des messages ; après un échec d'invitation du bot WhatsApp, `create` est quand même envoyé ; les résultats de `room_send`, `room_leave`, `room_forget` et `set_displayname` sont ignorés ; `ARNMessagerError` n'est pas interceptée | cdc §13 | Adaptateur qui vérifie chaque réponse `nio`, arrête la séquence sur erreur et journalise sans secret | 2 |
| L2-AM-021 | P1 | `main:441-460` | **NEW + INT** — les callbacks sont enregistrés avant la première synchronisation et `next_batch` n'est pas persisté : à chaque redémarrage, la timeline récente des salons rejoints est probablement relivrée aux callbacks, ce qui rejouerait les commandes `!am` (réinvitations, `create`, `set-pl`) | cdc §4.5 (reprise sûre), critère 11 | Ignorer les événements antérieurs au démarrage (synchronisation initiale sans callbacks, ou filtre par `server_timestamp`) ; option : persister `next_batch` dans `/data/session/` | 2 |
| L2-AM-022 | P2 | `message:178-300` | **NEW** — un seul bloc mêle parsing, autorisation, chaînes Mautrix, appels réseau, temporisations et messages | cdc §15 lot 2 (« séparation métier/Matrix/stockage ») | Fonctions de décision pures qui renvoient des `Action` ; exécution par un adaptateur | 2 |
| L2-AM-023 | P2 | `_:80-90`, `main:431-435` | **NEW** — état global `_.lang` ; `EXT_TO_LANG` non défini (`NameError` latent, masqué parce que `lang` a toujours une valeur par défaut) ; traduction `help`, `DEFAULT_MAUTRIX_BOT`, `DEFAULT_ANSWER_USERS`, `Callbacks.config_path`, `config['ask_portal_admin']` inutilisés ; `admins` calculé sans être utilisé dans `invite:156` | cdc §13 | Objet `Translator` injecté ; suppression du code mort ; branche d'extension de domaine supprimée | 2 |
| L2-AM-024 | P1 | `requirements.txt`, `main` | **CONF** — `matrix-nio[e2e]` et `python-olm` sont déclarés mais le store n'est jamais configuré ; les messages chiffrés arrivent en `MegolmEvent` et sont ignorés en silence | PF-AM-011 (E2EE hors POC, refus explicite) ; RT-AM-028 | Retirer `[e2e]`/`python-olm` ; callback `MegolmEvent` et détection `room.encrypted` → refus explicite, aucune commande traitée | 2 |
| L2-AM-025 | P1 | `requirements.txt` | **CONF + NEW** — `matrix-nio==0.20.1` ancien, `PyYAML==6.0` fragile, `wheel` inutile, `dnspython` à retirer, aucune version de Python déclarée, aucune dépendance de test | cdc §11, §13 | `pyproject.toml` ; dépendances épinglées (`matrix-nio` 0.25.x/0.26.x, `PyYAML>=6.0.1`) ; extras `test` ; version de Python selon A-06 | 2 |
| L2-AM-026 | P2 | `main` | **NEW** — pas de gestion de `SIGTERM`, `client.close()` n'est jamais appelé | RT-AM-011 (TO_VALIDATE) | `asyncio.run` ; gestionnaire `SIGTERM`/`SIGINT` → arrêt de la synchronisation, fermeture du client, sortie 0 | 2 |
| L2-AM-027 | P1 | `parse_args:323-326` | **NEW** — `basicConfig` au niveau racine : `-vv` active le DEBUG de `nio`/`aiohttp` (requêtes/réponses possibles) ; aucun format ; sans `-v`, niveau WARNING | cdc §13 ; RT-AM-063/064/066 | Configuration de logging dédiée : `nio`/`aiohttp` plafonnés à INFO ; filtre de rédaction (tokens `syt_…`, `Authorization`, clés `password`/`access_token`) | 2 |
| L2-AM-028 | P2 | `parse_args:309-336` | **NEW** — `-u` dérive un chemin de configuration depuis le MXID ; chemin par défaut `config.yml` dans le répertoire courant | RT-AM-014 (`/data/config.yml`, PROPOSED) vs PF-AM-010 (`/config/config.yml`, CONFIRMED) | `--config` avec le chemin par défaut arbitré (A-03) ; retrait de `-u` | 2 |
| L2-AM-029 | P1 | `main`, `load_config` | **NEW** — aucun code de sortie défini : une configuration invalide produit une trace Python (code 1 par accident) | RT-AM-013 (TO_VALIDATE) | Codes validés le 2026-11-06 (§10.4) : 0 arrêt normal, 1 erreur inattendue, 2 configuration invalide, 3 échec d'authentification ; à reporter dans le contrat avant E6 | 2 |
| L2-AM-030 | P2 | Commandes Mautrix (§3.6) | **CONF + INT** — les commandes `create`, `invite-link`, `delete-portal`, `unbridge`, `ping`, `sync` et `set-pl` existent bien (déclenchées par un humain) ; `upstream/testing` utilise `create-group`, `sync-portal` et `sync group`, signe d'une évolution des bridges ; le rôle déploie `dock.mau.dev/mautrix/{whatsapp,signal}:latest` | PF-AM-007 ; RT-AM-055 | Centraliser les chaînes sans les modifier ; compatibilité vérifiée avant le Lot 3 | 2 (centralisation) / 3 (validation) |
| L2-AM-031 | P2 | `message:261-300` | **NEW** — `!am <mxid>` est accessible à **tout** expéditeur du salon, puppets WhatsApp/Signal compris (c'est le parcours historique `ask_portal_admin`) : un correspondant externe peut faire inviter n'importe quel MXID d'un domaine autorisé avec le niveau 100 | cdc §4 (remplacé par identifiant + code), §7.1 (niveau 50) | Caractériser tel quel au Lot 2 ; remplacement au Lot 3 (A-02) | 3 |
| L2-AM-032 | P1 | `message:299-300` | **CONF** — promotion du propriétaire à 100 via `set-pl` | cdc §7.1 ; PF-AM §2 (BLOQUANT Lot 3) | Paramétrer le niveau (`power_levels`) sans en changer la valeur au Lot 2 ; passage à 50 au Lot 3 | 3 |
| L2-AM-033 | P2 | `message:194-199`, `:253-255` | **NEW** — `!am reset` n'exige pas `allowed` et vise toujours WhatsApp ; le relais `!wa`/`!sg` des `admins` lève `KeyError` si `admins` est absent | cdc §7.2 | Caractériser ; `admins` par défaut `[]` ; le sort des commandes historiques relève de A-02 | 2 |
| L2-AM-034 | P3 | `invite:171`, `TRANSLATIONS` | **NEW** — message français codé en dur hors i18n, mentionnant `@sans-nuage.fr` | cdc §13 | Nouvelle clé de traduction paramétrée | 2 |
| L2-AM-035 | P2 | `README.md` | **NEW** — installation systemd, login interactif, `sans-nuage.fr` | cdc §10 (documentation de session) | Réécriture minimale et `docs/CONFIGURATION.md` + `docs/SESSION.md` | 2 (doc) / 4 (conteneur) |
| L2-AM-036 | P3 | `invite:156`, `message:184`, `:232` | **NEW** — « admin » signifie niveau ≥ 100 lu dans le cache `nio`, qui peut être obsolète juste après une jonction | cdc §7 | Caractériser ; seuil lu depuis `power_levels.technical` | 2 / 3 |
| L2-AM-037 | P3 | `LICENSE` | **NEW** — AGPLv3 : la publication d'une image implique de rendre le source disponible | cdc §11 | Conserver la licence et les en-têtes ; rappel pour le Lot 4 | 4 |
| L2-AM-038 | — | `requirements.txt` | **CONF** — aucune dépendance PostgreSQL | cdc §9 | Rien au Lot 2 | 3 |
| L2-AM-039 | — | Commandes `!am code…` | **CONF** — absentes | cdc §4, §8 | Rien au Lot 2 | 3 |

**Total : 39 constats**, dont 32 relèvent (au moins en partie) du Lot 2.

### 4.2 Synthèse par catégorie de vérification

| Catégorie | Constats |
|---|---|
| Confirmés (préflight) | 004, 005, 008, 009, 012 (compte corrigé : 7 au lieu de 4), 014, 017, 024, 025, 030, 032, 038, 039 |
| Infirmés ou corrigés | 012 (nombre de `sleep`), 018 (`logger.debug(resp)` ne peut pas contenir de token), 020 (trois cas d'erreur gérés, pas un seul) |
| Nouveaux | 001, 002, 003, 006, 007, 010, 011, 013, 015, 016, 019, 021, 022, 023, 026, 027, 028, 029, 031, 033, 034, 035, 036, 037 |
| Nécessitent un test d'intégration | 011 (motifs des puppets), 013 (séquencement des callbacks), 021 (rejeu au redémarrage), 030 (commandes Mautrix), comportement de `sync_forever` sur token révoqué (RT-AM-044) |

---

## 5. Architecture cible limitée au Lot 2

L'objectif est minimal : un petit package Python, sans framework
supplémentaire, sans persistance métier. Chaque module a une responsabilité
unique et testable.

```text
pyproject.toml
config.example.yml
src/arn_messager/
  __init__.py
  __main__.py        CLI : arguments, logging, asyncio.run, signaux, codes de sortie
  config.py          chargement YAML strict → dataclasses figées ; lecture des fichiers secrets à la demande
  mxid.py            parse_mxid(), validation du nom de serveur, appartenance à allowed_domains
  logs.py            configuration du logging, filtre de rédaction des secrets
  i18n.py            Translator (langue injectée, sans état global)
  mautrix.py         construction des commandes par réseau (préfixe, verbe, arguments) ; délais nommés
  actions.py         dataclasses : SendText, Invite, Join, Leave, Forget, Wait
  decisions.py       fonctions pures : on_invite(snapshot, event, cfg) / on_message(...) → list[Action]
  matrix_gateway.py  adaptateur mince sur nio.AsyncClient : exécute les actions, vérifie les réponses
  session.py         SessionStore : lecture/écriture atomique de /data/session (0600/0700)
  auth.py            stratégie de connexion : session valide → login par fichier → une seule réauthentification
  bot.py             assemblage : callbacks nio → snapshot → decisions → gateway ; filtre de démarrage
tests/
  legacy/            tests de caractérisation sur arn-messager.py (supprimés en fin de lot)
  unit/              mxid, config, i18n, mautrix, decisions, session, logs
  async/             gateway, auth, bot (AsyncMock de nio)
  security/          non-divulgation des secrets
  fixtures/          configurations valides et invalides
arn-messager.py      supprimé en fin de lot, sans shim (A-07)
```

### 5.1 Responsabilités

- **`decisions.py`** est le cœur testable. Il reçoit un `RoomSnapshot`
  (identifiant, membres, niveaux de pouvoir, chiffré ou non), l'événement
  (expéditeur, corps, `state_key`) et la configuration, puis renvoie une liste
  ordonnée d'`Action`. Il n'importe pas `nio`. Les délais de bridge y sont des
  `Wait(seconds)` explicites, ce qui permet de vérifier la séquence sans
  attendre.
- **`matrix_gateway.py`** exécute les actions dans l'ordre : `Wait` devient
  `asyncio.sleep`, et chaque réponse `nio` est contrôlée. Une erreur
  interrompt la séquence et est journalisée sans secret.
- **`auth.py`** implémente exactement RT-AM-044 : session valide (vérifiée par
  `whoami`) → token réutilisé et mot de passe jamais lu ; session absente →
  login avec le fichier secret puis écriture atomique ; token invalide en
  cours de fonctionnement → état non prêt, **une** réauthentification, sinon
  sortie avec le code 3.
- **`bot.py`** n'enregistre les callbacks qu'après une synchronisation
  initiale, ou ignore les événements antérieurs au démarrage (L2-AM-021). Il
  expose un petit objet d'état (dernière synchronisation réussie, session
  prête) qui servira au healthcheck du Lot 4, sans l'implémenter.

### 5.2 Points d'extension préparés pour le Lot 3 (sans implémentation)

- `decisions.py` accueillera les commandes `!am code/codes/revoke/admin`
  comme de nouvelles fonctions pures.
- `config.py` valide déjà `claims`, `power_levels` et `postgresql`.
- La dépendance PostgreSQL (`asyncpg` ou `psycopg`) sera ajoutée au Lot 3,
  derrière une interface de stockage définie à ce moment-là, pas avant.

### 5.3 Ce que le Lot 2 ne fait pas

Pas d'injection de dépendances par framework, pas de bus d'événements, pas de
plugins, pas de parallélisation des callbacks, pas de base de données.

---

## 6. Plan d'exécution ordonné

Les commits C1 à C17 sont les commits prévus par le plan, un par étape (E1
à E17). Une étape peut exceptionnellement nécessiter plusieurs commits
atomiques ; ils sont alors proposés par Claude et exécutés exclusivement par
l'utilisateur humain (voir §8). Une étape n'est engagée que si les tests de
l'étape précédente passent.

### E0 — Arbitrages préalables (sans commit de code) — **VALIDÉE le 2026-11-06**

- **Objectif** : lever A-01 (base du fork), A-03 (chemin de configuration),
  A-04 (clés optionnelles), A-06 (version de Python) ; prendre acte de A-02,
  A-05 et A-07.
- **Fichiers** : ce document uniquement (consignation des décisions).
- **Prérequis** : validation de ce plan.
- **Critère de validation** : décisions consignées dans ce document ;
  report dans le contrat runtime avant E6 (§10.5).
- **Résultat** : A-01 à A-08 validés (§10.1) ; orientations P1 à P5
  acceptées (§10.3) ; codes de sortie confirmés (§10.4). Le risque d'origine
  (rejouer E2 et E3 si `upstream/testing` était retenu) est levé par A-01.

### E1 — Outillage de test et `.gitignore`

- **Objectif** : pouvoir exécuter `pytest` sans modifier le comportement.
- **Fichiers** : `.gitignore`, `pyproject.toml` (métadonnées,
  `requires-python = ">=3.10"` selon A-06, extras `test` : `pytest`,
  `pytest-asyncio` ; dépendances d'exécution **inchangées** à ce stade),
  `tests/conftest.py` minimal, **sans** faux objets `matrix-nio` (reportés
  en E3, décision du 2026-11-06).
- **Modifications** : `.gitignore` ciblé (L2-AM-002).
- **Prérequis** : E0.
- **Tests** : un test trivial de collecte ; `python -m compileall arn-messager.py`.
- **Validation** : `pytest` est vert ; `git status` montre que les fichiers
  YAML d'exemple ne sont plus ignorés.
- **Risques** : faibles.
- **Dépendances** : aucune.
- **Commit** : C1.

### E2 — Garde d'import

- **Objectif** : rendre `arn-messager.py` chargeable par les tests
  (L2-AM-003) sans rien changer d'autre.
- **Fichiers** : `arn-messager.py` (dernière ligne sous
  `if __name__ == "__main__":`).
- **Tests** : chargement via `importlib.util.spec_from_file_location` sans
  exécution de `main()`.
- **Validation** : le diff fait deux lignes ; le lancement manuel reste
  identique.
- **Risques** : nuls.
- **Commit** : C2.

### E3 — Tests de caractérisation de l'existant

- **Objectif** : figer le comportement historique avant toute refactorisation.
- **Fichiers** : `tests/conftest.py` (ajout des faux objets `matrix-nio` :
  `Room`, événements, réponses ; reportés de E1, décision du 2026-11-06),
  `tests/legacy/test_invite.py`, `test_message.py`, `test_config.py`,
  `test_i18n.py`, `test_login.py`.
- **Méthode** : `AsyncClient` remplacé par un `AsyncMock` qui enregistre les
  appels ; `sleep` du module remplacé par un enregistreur ; configuration
  équivalente à l'installation d'origine (`sans-nuage.fr`) ; assertions sur la
  **séquence exacte** d'appels (`room_send` avec corps, `room_invite`,
  `room_leave`, `room_forget`) et sur les délais demandés.
- **Scénarios minimaux** (voir section 7.1) : 20 à 25 cas, y compris les
  défauts connus. Ces derniers sont marqués `@pytest.mark.legacy_defect` et
  documentés : ils seront inversés par le commit qui corrige le défaut.
- **Validation** : tous les tests sont verts contre `8705fa8` + E2.
- **Risques** : faux objets trop éloignés de l'API réelle de `matrix-nio`,
  couverts par le test d'import d'E4 et par I-1. (Le risque d'origine,
  caractériser une base abandonnée, est levé par A-01.)
- **Commit** : C3.

### E4 — Dépendances

- **Objectif** : sortir de `matrix-nio` 0.20.1 et de l'E2EE avant d'écrire du
  nouveau code (L2-AM-024, L2-AM-025).
- **Fichiers** : `pyproject.toml` (dépendances d'exécution épinglées),
  `requirements.txt` (traitement à décider, voir prérequis).
- **Prérequis** : décision du propriétaire, avant l'exécution d'E4, sur le
  maintien, la génération ou la suppression de `requirements.txt` (point
  non couvert par A-07, qui ne concerne que `arn-messager.py`).
- **Modifications** : `matrix-nio` 0.25.x/0.26.x sans `[e2e]`,
  `PyYAML>=6.0.1,<7`, retrait de `python-olm` et `wheel` ; `dnspython`
  conservé jusqu'à E6.
- **Tests** : les tests de caractérisation doivent rester verts ; test
  d'import de `nio` et des classes utilisées (`AsyncClient`, `LoginResponse`,
  `RoomMessageText`, `InviteMemberEvent`, `JoinError`, `RoomInviteError`,
  `MegolmEvent`).
- **Validation** : installation propre dans un venv neuf sans `libolm`.
- **Risques** : changement d'API de `nio` non couvert par les mocks. On les
  détecte par le test d'intégration I-1 (section 7.6) avant la fin du lot.
- **Commit** : C4.

### E5 — Package et analyse des MXID

- **Objectif** : créer `src/arn_messager/` et le premier module pur (L2-AM-008,
  009, 010).
- **Fichiers** : `src/arn_messager/__init__.py`, `mxid.py`,
  `tests/unit/test_mxid.py`.
- **Modifications** : `parse_mxid(s) -> Mxid(localpart, server_name)` selon la
  grammaire Matrix (localpart `[a-z0-9._=\-/+]`, nom de serveur avec port
  optionnel, IPv6 entre crochets) ; `is_allowed(mxid, allowed_domains)` par
  égalité exacte, insensible à la casse pour le nom d'hôte.
- **Tests** : table de cas valides et invalides, notamment
  `@x:evilsans-nuage.fr`, `@a:b:domaine`, `@bot:hote:8448`, espaces, chaînes
  vides et Unicode.
- **Validation** : couverture ≥ 95 % du module.
- **Risques** : trop de rigueur, qui rejetterait des MXID historiques
  (localparts majuscules). À documenter.
- **Commit** : C5.

### E6 — Configuration stricte (schéma du contrat)

- **Objectif** : L2-AM-006, 014, 015, 028 (partie chemin).
- **Fichiers** : `config.py`, `config.example.yml`,
  `tests/unit/test_config.py`, `tests/fixtures/*.yml`.
- **Modifications** : `yaml.safe_load` ; dataclasses figées `MatrixConfig`,
  `SecretsConfig`, `NetworkConfig`, `ClaimsConfig`, `PowerLevelsConfig`,
  `PostgresConfig`, `Config` ; toutes les erreurs agrégées dans une seule
  `ConfigError` ; clés inconnues refusées (A-08) ; au moins un réseau activé ;
  `puppet_regex` compilé avec `re.fullmatch` ; cohérence
  `power_levels.owner < power_levels.technical`,
  `claims.max_* ≥ 1`, TTL > 0 ; chemins des fichiers secrets vérifiés
  (existence, lisibilité) **sans lire leur contenu** au chargement ;
  suppression de la découverte DNS et de `dnspython`.
- **Tests** : configuration valide minimale, configuration complète du
  contrat §12, chacune des erreurs, fichier absent, fichier vide, YAML
  invalide, clé inconnue, aucun réseau activé. Le message d'erreur ne contient
  jamais le contenu d'un fichier secret.
- **Validation** : l'exemple du contrat §12 se charge sans erreur.
- **Prérequis** : contrat runtime harmonisé et validé par le propriétaire
  (§10.5) ; valeurs par défaut de `bot.*` documentées (A-04).
- **Risques** : écart entre le schéma retenu et le template Ansible du Lot 5,
  couvert par A-04 et l'harmonisation préalable du contrat.
- **Dépendances** : E5.
- **Commit** : C6.

### E7 — Journalisation sans secrets

- **Objectif** : L2-AM-018, 019, 027.
- **Fichiers** : `logs.py`, `tests/security/test_logging.py`.
- **Modifications** : `setup_logging(verbosity)` ; loggers `nio`, `aiohttp` et
  `peewee` plafonnés ; `RedactingFilter` (motifs `syt_[A-Za-z0-9_]+`,
  `Bearer …`, `"password": …`, `"access_token": …`) ; format
  `%(asctime)s %(levelname)s %(name)s %(message)s` (RT-AM-064 proposé) ;
  règle : aucun corps de message journalisé.
- **Tests** : `caplog` sur des chaînes contenant des tokens factices ;
  vérification que `nio` n'émet pas de DEBUG avec `-vv`.
- **Validation** : aucun secret factice retrouvé dans les journaux capturés
  pendant toute la suite de tests (fixture globale, cf. 7.5).
- **Commit** : C7.

### E8 — i18n sans état global

- **Objectif** : L2-AM-023, 034.
- **Fichiers** : `i18n.py`, `tests/unit/test_i18n.py`.
- **Modifications** : `Translator(lang)` ; traductions reprises à l'identique ;
  nouvelle clé pour le message de refus (`:171`), paramétrée par les domaines
  autorisés ; suppression de `EXT_TO_LOCALE`, de `help` inutilisé et des
  constantes mortes.
- **Tests** : repli `fr_FR` → `en_US` → identifiant ; paramètres manquants.
- **Commit** : C8.

### E9 — Commandes Mautrix centralisées

- **Objectif** : L2-AM-007, 030 (centralisation).
- **Fichiers** : `mautrix.py`, `tests/unit/test_mautrix.py`.
- **Modifications** : `BridgeCommands(network_cfg)` avec des méthodes
  `set_relay()`, `create()`, `invite_link()`, `delete_portal()`, `ping()`,
  `unbridge()`, `sync()`, `set_power_level(mxid, level)`, `reconnect()`,
  `raw(text)` ; verbes **identiques** à `8705fa8` ; préfixe issu de la
  configuration ; délais historiques (3 s et 7 s) en constantes nommées.
- **Tests** : chaînes produites pour WhatsApp et Signal avec des préfixes
  personnalisés.
- **Commit** : C9.

### E10 — Extraction des décisions (iso-fonctionnelle)

- **Objectif** : L2-AM-022, 004, 005, 036.
- **Fichiers** : `actions.py`, `decisions.py`, `tests/unit/test_decisions.py`
  (portage des scénarios de `tests/legacy/` sur des fonctions pures).
- **Modifications** : `on_invite()` et `on_message()` reproduisent exactement
  la séquence de `Callbacks.invite`/`message`, y compris `reconnect` et les
  `Wait`, avec `technical_accounts` et `allowed_domains` à la place des
  valeurs en dur. Les défauts `legacy_defect` sont **conservés** dans ce
  commit.
- **Tests** : chaque scénario de caractérisation a son équivalent pur ; les
  deux suites passent.
- **Validation** : le diff des séquences attendues entre `legacy` et `unit`
  est vide.
- **Risques** : glissement de comportement pendant l'extraction, couvert par
  la double suite.
- **Dépendances** : E6, E8, E9.
- **Commit** : C10.

### E11 — Corrections de sécurité du parsing et de l'autorisation

- **Objectif** : L2-AM-008, 009, 010, 011, 033 (partie `KeyError`).
- **Fichiers** : `decisions.py`, tests.
- **Modifications** : utilisation de `parse_mxid`/`is_allowed` partout ;
  puppets par `fullmatch` ; `admins` vide par défaut. **Aucune** modification
  des règles métier (qui peut faire quoi) en dehors de la correction du
  suffixe.
- **Tests** : inversion explicite des tests `legacy_defect` concernés
  (message de commit listant chaque test inversé).
- **Commit** : C11.

### E12 — Adaptateur Matrix, attentes asynchrones et erreurs

- **Objectif** : L2-AM-012, 020.
- **Fichiers** : `matrix_gateway.py`, `tests/async/test_gateway.py`.
- **Modifications** : exécution séquentielle des `Action` ; `Wait` →
  `asyncio.sleep` ; contrôle de chaque réponse (`JoinError`,
  `RoomInviteError`, `RoomSendError`, `RoomLeaveError`…) ; arrêt de la
  séquence sur erreur, avec message de bridge préfixé comme dans l'existant
  (pour ne pas le relayer côté WhatsApp) ; `join` avec 3 essais espacés.
- **Tests** : `AsyncMock` ; `asyncio.sleep` patché pour vérifier les durées ;
  test garde-fou qui échoue si `time.sleep` est importé dans le package
  (analyse AST de `src/`).
- **Validation** : `grep -rn "time.sleep\|from time import sleep" src/` est
  vide.
- **Commit** : C12.

### E13 — Session et authentification

- **Objectif** : L2-AM-016, 017 ; RT-AM-020/022/024/044.
- **Fichiers** : `session.py`, `auth.py`, `tests/unit/test_session.py`,
  `tests/async/test_auth.py`.
- **Modifications** : `SessionStore(dir)` : `session.json`
  (`user_id`, `device_id`, `access_token`, `homeserver_url`, `created_at`),
  écriture atomique en 0600 dans un répertoire en 0700, contrôle des
  permissions à la lecture (avertissement si trop ouvertes) ; `auth.py` :
  `whoami` pour valider une session, login par fichier secret (contenu retiré
  des espaces de fin, jamais journalisé), une seule réauthentification,
  `AuthError` → code 3 ; `device_name` stable (configuration ou valeur fixe,
  plus de hasard à chaque démarrage).
- **Tests** : session absente, valide, invalide avec réauthentification
  réussie, réauthentification échouée (code 3, aucun secret dans les
  journaux), fichier corrompu, permissions ; le fichier de configuration
  n'est jamais ouvert en écriture (vérification par mock de `open`).
- **Risques** : gestion du token révoqué pendant `sync_forever` (voir
  L2-AM-021 et I-3) ; détection du `M_UNKNOWN_TOKEN` à confirmer contre
  `nio` 0.25+.
- **Dépendances** : E4, E6, E7.
- **Commit** : C13.

### E14 — Boucle principale, arrêt propre, non-rejeu

- **Objectif** : L2-AM-003 (fin), 021, 026, 028, 029.
- **Fichiers** : `__main__.py`, `bot.py`, `tests/async/test_bot.py`,
  `tests/unit/test_cli.py`.
- **Modifications** : `python -m arn_messager --config PATH [-v|-vv]` ;
  `asyncio.run` ; `SIGTERM`/`SIGINT` → arrêt propre ; synchronisation
  initiale, puis enregistrement des callbacks (ou filtre par horodatage) ;
  codes de sortie 0, 1, 2 et 3 (§10.4) ; objet d'état (dernière synchronisation
  réussie).
- **Tests** : configuration invalide → code 2 ; échec d'authentification →
  code 3 ; événements de la synchronisation initiale non traités ; `SIGTERM`
  simulé → `client.close()` appelé.
- **Commit** : C14.

### E15 — Refus des salons chiffrés

- **Objectif** : L2-AM-024 ; PF-AM-011.
- **Fichiers** : `decisions.py`, `bot.py`, tests.
- **Modifications** : sur `MegolmEvent` ou dans un salon `encrypted`, aucune
  commande n'est traitée et un message explicite, non chiffré, est envoyé
  (au plus une fois par salon et par démarrage). La création d'une
  antichambre de remplacement relève du Lot 3 (PF-AM-013).
- **Tests** : salon chiffré → une seule notification, aucune autre action.
- **Point ouvert (P4, §10.3)** : l'envoi de cette notification n'est pas
  validé techniquement ; il est à trancher par le propriétaire avant E15.
  Seul le non-traitement des commandes est acquis.
- **Commit** : C15.

### E16 — Retrait de l'existant et documentation

- **Objectif** : L2-AM-035 ; clôture de la double suite.
- **Fichiers** : suppression de `arn-messager.py` (sans shim, A-07), de
  `tests/legacy/` et de `arn-messager_domain.tld.yml` ; `README.md`,
  `docs/CONFIGURATION.md`, `docs/SESSION.md` (création du compte, premier
  login, révocation et renouvellement, perte du volume : cdc §10,
  RT-AM-030).
- **Tests** : la suite `unit/async/security` reste verte ; les scénarios
  historiques y sont couverts (table de correspondance dans le message de
  commit).
- **Commit** : C16.

### E17 — Intégration continue

- **Objectif** : exécuter automatiquement les tests (cdc §13).
- **Fichiers** : `.github/workflows/tests.yml` (dépôt `origin` sur GitHub) :
  installation, `pytest`, `compileall` ; matrice Python 3.10 et 3.12 (A-06).
- **Validation** : pipeline vert sur la branche `lot-2-refactorisation`.
- **Commit** : C17.

**Total : 18 étapes (E0 à E17), dont 17 donnent lieu à un commit.**

---

## 7. Stratégie de tests

### 7.1 Tests de caractérisation de l'existant (E3)

Ils portent sur `arn-messager.py` au commit `8705fa8` + garde d'import. Le
client est un `AsyncMock` et `sleep` est patché.

| # | Scénario | Résultat attendu (existant) |
|---|---|---|
| C-01 | Invitation par un expéditeur hors `botusers` | Aucune action, WARNING |
| C-02 | Invitation dont `state_key` n'est pas le bot | Aucune action |
| C-03 | Invitation par le bot WhatsApp | `join`, `!wa reconnect`, `sleep(3)`, `!wa set-relay`, `ask_portal_admin` |
| C-04 | Invitation par le bot Signal | `join`, `!wa reconnect`, `!sg set-relay`, `ask_portal_admin` |
| C-05 | Invitation par l'unique humain du domaine autorisé | `join`, `reconnect`, `ask_im` |
| C-06 | Invitation par un humain alors qu'un second humain est présent | Message FR de refus, `sleep(3)`, `leave`, `forget` |
| C-07 | Échec de `join` trois fois | ERROR journalisé, puis envoi de messages malgré tout (`legacy_defect`) |
| C-08 | `!am whatsapp` autorisé | Invitation du bot, `create`, `set-relay`, `invite-link`, délais 3/3/7 |
| C-09 | `!am whatsapp` avec `RoomInviteError` | Message d'erreur préfixé, puis `create` envoyé quand même (`legacy_defect`) |
| C-10 | `!am whatsapp` non autorisé (deux humains) | Pas de commande de bridge ; retombe dans le parsing `!am <mxid>` sans correspondance |
| C-11 | `!am ciao whatsapp`, `!am ping whatsapp` | `delete-portal`, `ping` |
| C-12 | `!am signal` avec le bot Signal au niveau 100 | `invite-link` |
| C-13 | `!am signal` sans le bot Signal au niveau 100 | Message `signal_missing_bridge` avec `bot_number` |
| C-14 | `!am unbridge signal`, `!am ciao signal`, `!am sync signal` | `unbridge`, `delete-portal`, `sync` |
| C-15 | `!am reset` par un utilisateur non « allowed » | `set-relay` WhatsApp envoyé (`legacy_defect`) |
| C-16 | Relais `!wa …` par un admin ; par un non-admin | Relayé ; ignoré |
| C-17 | `!am @alice:sans-nuage.fr` envoyé par un puppet WhatsApp | `!wa set-pl <bot> 100`, `invite`, `invited`, `!wa`/`!sg set-pl alice 100` |
| C-18 | `!am alice@sans-nuage.fr` | Converti en `@alice:sans-nuage.fr` |
| C-19 | `!am @bot:sans-nuage.fr` (le bot lui-même) | Aucune invitation |
| C-20 | `!am @x:evilsans-nuage.fr` / `!am @a:b:sans-nuage.fr` avec `botusers=["sans-nuage.fr"]` | Premier refusé par la regex ; second **accepté** et invité tel quel (`legacy_defect`) — vérifié par exécution isolée de la regex |
| C-21 | Expéditeur `@x:evilsans-nuage.fr` et `!am whatsapp` | Passe le filtre `endswith` (`legacy_defect`) |
| C-22 | Invitation échouée (`RoomInviteError`) sur `!am <mxid>` | Message préfixé `!wa` |
| C-23 | Message émis par le bot lui-même | Ignoré |
| C-24 | `load_config` : fichier absent, fichier vide, `server` absent | Valeurs par défaut, `AttributeError`, résolution DNS (mockée) |
| C-25 | `ask_password` : un échec puis un succès | Deux appels à `login` ; configuration réécrite avec le token (`legacy_defect`) |

### 7.2 Tests unitaires

`mxid`, `config`, `i18n`, `mautrix`, `decisions`, `session`, `logs` sont des
fonctions pures ou des E/S locales dans `tmp_path`. `decisions` rejoue les
scénarios C-01 à C-23 sous forme de listes d'`Action`.

### 7.3 Tests asynchrones

Avec `pytest-asyncio` et `AsyncMock` de `nio.AsyncClient` :

- `matrix_gateway` : ordre d'exécution, `asyncio.sleep` appelé avec les bonnes
  durées, arrêt sur chaque type d'erreur ;
- `auth` : les quatre branches de RT-AM-044 ;
- `bot` : filtre de démarrage, arrêt sur signal, mise à jour de l'état de
  synchronisation ;
- garde-fou : aucun `time.sleep` dans `src/` (analyse AST).

### 7.4 Tests de configuration

Pour chaque champ obligatoire du mapping du contrat §13 : absence → erreur
nommée. S'y ajoutent les types, les bornes (TTL, compteurs), la cohérence des
niveaux 50/100, au moins un réseau activé, le regex invalide, la clé inconnue,
le fichier secret absent ou illisible, et le chargement de l'exemple exact du
contrat §12.

### 7.5 Tests de sécurité et de non-divulgation

- Fixture globale : les valeurs secrètes factices (`MOT-DE-PASSE-TEST`,
  `syt_FAUX_TOKEN_TEST`) ne doivent apparaître dans **aucun** enregistrement
  de log capturé, sur toute la suite.
- Les messages de `ConfigError` et `AuthError` ne contiennent pas le contenu
  des fichiers secrets.
- `repr()`/`str()` des dataclasses de configuration et de session masquent le
  token.
- `session.json` est créé en 0600 dans un répertoire 0700, et l'écriture est
  atomique (aucun fichier partiel en cas d'exception simulée).
- Aucun corps de message n'est journalisé (préparation du critère 2 du cdc
  §14).
- Le fichier de configuration n'est jamais ouvert en écriture.

### 7.6 Tests nécessitant un vrai serveur Matrix (protocole futur, non exécutés)

Environnement proposé : Synapse local jetable (`matrixdotorg/synapse`,
inscription par secret partagé) sur un poste de développement, **jamais** sur
les serveurs de staging ou de production sans accord explicite.

| ID | Protocole | Critère |
|---|---|---|
| I-1 | Démarrer le bot avec un fichier de mot de passe et un `/data/session` vide | Login réussi, `session.json` en 0600, aucun secret dans stdout/stderr |
| I-2 | Redémarrer | Token réutilisé, fichier de mot de passe non lu (retirer ses droits de lecture pour le prouver) |
| I-3 | Révoquer le token par l'API d'administration pendant l'exécution | Une seule réauthentification ; synchronisation reprise ; puis, avec un mauvais mot de passe : sortie avec le code 3 |
| I-4 | Envoyer `!am …` dans un salon, arrêter le bot, le redémarrer | La commande n'est pas rejouée (L2-AM-021) |
| I-5 | Inviter le bot par un compte autorisé, puis par un compte non autorisé | Comportements C-05 et C-01 |
| I-6 | Salon chiffré | Refus explicite, aucune commande traitée |
| I-7 | Configuration invalide | Code 2, message explicite |
| I-8 | `SIGTERM` | Sortie 0 en moins de 10 s, client fermé |
| I-9 | Mesure | Aucun blocage de la boucle > 100 ms pendant `!am whatsapp` (débogage asyncio `loop.slow_callback_duration`) |

Ces tests doivent être réalisés avant la déclaration de fin du Lot 2 (critère
S-10). Ils ne l'ont pas été à la date de ce document.

### 7.7 Tests Mautrix reportés avant le Lot 3 (PF-AM-006, PF-AM-007)

À réaliser contre les **versions réellement déployées** des bridges, qui
doivent d'abord être épinglées (le rôle utilise `tag: latest`) :

1. Nom et syntaxe actuels de chaque commande : `set-relay`, `create` ou
   `create-group`, `invite-link`, `delete-portal`, `unbridge`, `ping`, `sync`
   ou `sync-portal`, `set-pl`, `reconnect`.
2. Format réel des puppets WhatsApp et Signal (`puppet_regex`).
3. Création et exposition du salon-portail quand un correspondant contacte le
   numéro partagé ; invitation d'ARN-Messager dans ce salon.
4. Possibilité de déclencher `delete-portal`/`unbridge` sans action humaine
   (expiration, cdc §5.3).
5. Niveaux de pouvoir : protocole en 6 étapes du préflight §6 (promotion par
   `!am admin` uniquement).
6. Réponses textuelles du bot de bridge exploitables pour remplacer les délais
   fixes (L2-AM-013).

---

## 8. Séquence de commits proposée

Aucun de ces commits n'est créé par cette intervention. Les messages de
commit sont proposés par Claude sans ligne Co-Authored-By ni signature
d'assistance IA. Les commits sont exclusivement exécutés par l'utilisateur
humain.

| # | Message proposé | Contenu exact | Tests devant réussir |
|---|---|---|---|
| C1 | `chore: add pytest tooling and narrow .gitignore` | `pyproject.toml` (métadonnées, extras `test`, dépendances d'exécution inchangées), `tests/conftest.py` minimal sans faux objets `matrix-nio`, `.gitignore` | `pytest` (collecte), `compileall` |
| C2 | `refactor: guard entry point to allow importing the module` | `arn-messager.py` : `if __name__ == "__main__":` | Test de chargement du module |
| C3 | `test: characterize legacy bot behaviour at 8705fa8` | `tests/conftest.py` (faux objets `matrix-nio`), `tests/legacy/*` (C-01 à C-25) | Suite `legacy` complète |
| C4 | `build: pin runtime dependencies and drop E2EE extras` | `pyproject.toml`, `requirements.txt` | `legacy` + test d'import `nio` |
| C5 | `feat(mxid): add structured Matrix ID parsing` | `src/arn_messager/__init__.py`, `mxid.py`, `tests/unit/test_mxid.py` | `legacy` + `unit/test_mxid` |
| C6 | `feat(config): strict config loader aligned with runtime contract` | `config.py`, `config.example.yml`, tests et fixtures ; retrait de `dnspython` | `legacy` + `unit` |
| C7 | `feat(logs): logging setup with secret redaction` | `logs.py`, `tests/security/test_logging.py` | `legacy` + `unit` + `security` |
| C8 | `refactor(i18n): stateless translator` | `i18n.py`, tests | idem |
| C9 | `refactor(mautrix): centralize bridge command strings per network` | `mautrix.py`, tests | idem |
| C10 | `refactor: extract pure decision functions from callbacks` | `actions.py`, `decisions.py`, `tests/unit/test_decisions.py` | `legacy` + `unit` : séquences identiques |
| C11 | `fix: parse MXIDs and domains instead of suffix matching` | `decisions.py`, inversion des tests `legacy_defect` concernés (liste dans le corps du message) | `unit` + `security` ; `legacy` adapté |
| C12 | `refactor: async Matrix gateway without blocking sleeps` | `matrix_gateway.py`, `tests/async/test_gateway.py`, garde-fou AST | Toutes les suites |
| C13 | `feat(session): file-based session store and non-interactive auth` | `session.py`, `auth.py`, tests | Toutes les suites |
| C14 | `feat: asyncio.run entry point, graceful shutdown, no event replay` | `__main__.py`, `bot.py`, tests CLI et bot | Toutes les suites |
| C15 | `feat: refuse commands in encrypted rooms` | `decisions.py`, `bot.py`, tests | Toutes les suites |
| C16 | `chore: remove legacy script and document configuration and session` | Suppression de `arn-messager.py` (sans shim), `tests/legacy/`, exemple vide ; `README.md`, `docs/CONFIGURATION.md`, `docs/SESSION.md` | `unit` + `async` + `security` |
| C17 | `ci: run test suite on GitHub Actions` | `.github/workflows/tests.yml` | Pipeline vert |

**Total : 17 commits.**

---

## 9. Critères de sortie du Lot 2

| # | Critère | Moyen de vérification |
|---|---|---|
| S-01 | Les comportements historiques conservés sont couverts par des tests, avec une table de correspondance C-xx → test unitaire | Revue du message de C16 ; `pytest` |
| S-02 | Aucune occurrence de `sans-nuage`, `89.234.141.66` ou `mautrix_admin` dans `src/` et `tests/unit` | `grep -rn` vide |
| S-03 | Aucun préfixe `!wa`/`!sg` en dur dans `src/` (hors exemples et tests) | `grep` + revue |
| S-04 | Aucune comparaison `endswith`/`split(':')` sur des MXID dans `src/` | `grep` + tests `mxid` |
| S-05 | Aucun `time.sleep` dans `src/` | Test garde-fou AST |
| S-06 | Configuration invalide → code de sortie 2 et message explicite, sans trace Python | Tests CLI + I-7 |
| S-07 | Aucun secret factice dans les journaux sur toute la suite ; aucun corps de message journalisé | Fixture de sécurité |
| S-08 | Le fichier de configuration n'est jamais écrit ; session dans `/data/session/` en 0600/0700, écriture atomique | Tests `session` + I-1 |
| S-09 | `decisions.py` n'importe pas `nio` et est couvert à ≥ 90 % | Analyse d'import + couverture |
| S-10 | Tests d'intégration I-1 à I-9 exécutés sur un Synapse local, avec résultats consignés | Compte rendu joint |
| S-11 | CI verte sur `lot-2-refactorisation` | GitHub Actions |
| S-12 | `docs/CONFIGURATION.md` et `docs/SESSION.md` présents ; le contrat runtime a été harmonisé **avant E6** pour les décisions A-03, A-04, A-08 et les codes de sortie (§10.5), et reste cohérent avec l'implémentation finale | Revue |
| S-13 | Aucune fonctionnalité du Lot 3 introduite (pas de `!am code`, pas de PostgreSQL, niveau du propriétaire inchangé et paramétré) | Revue du diff |
| S-14 | Les points d'extension du Lot 3 sont identifiés dans `decisions.py` et `config.py` | Revue |

---

## 10. Risques, blocages et arbitrages

### 10.1 Arbitrages

Tous les arbitrages ont été validés par le propriétaire le 2026-11-06. La
colonne « Recommandation » est conservée dans sa rédaction d'origine ; la
colonne « État » consigne la décision.

| ID | Point | Exigences en présence | Recommandation | État |
|---|---|---|---|---|
| A-01 | Base du fork : `master`/`8705fa8` ou `upstream/testing` | Consigne : commit de référence `8705fa8` ; préflight et contrat établis sur `master` ; mais `upstream/testing` (31 commits, 2026-01) corrige une partie des défauts et suit les bridges récents | **Rester sur `8705fa8`** (base auditée, plus simple, sans la régression `event.body` ni le mot de passe en clair dans la configuration). Consulter `testing` comme **source d'information** pour PF-AM-007 (noms de commandes bridgev2, motif `@whatsapp_lid-`), sans fusion. | **VALIDÉ (2026-11-06)** — base `8705fa8`, aucune fusion de `upstream/testing` ; ses commits peuvent être étudiés individuellement |
| A-02 | Avenir des commandes historiques (`!am whatsapp/signal/ciao/sync/ping/reset`, relais admin, `!am <mxid>`) | cdc §8 (liste minimale qui ne les mentionne pas) vs objectif du Lot 2 (préserver le comportement) | Les conserver toutes au Lot 2 ; décider au démarrage du Lot 3 lesquelles disparaissent (`!am <mxid>` est a priori remplacé par §4) | **VALIDÉ (2026-11-06)** — commandes historiques conservées et caractérisées pendant le Lot 2 ; leur sort est décidé au Lot 3 |
| A-03 | Chemin du fichier de configuration dans le conteneur | RT-AM-014 (PROPOSED) : `/data/config.yml` ; PF-AM-010 et contrat §4 (CONFIRMED) : `/config/config.yml` | `/config/config.yml` (décision CONFIRMED la plus récente) ; corriger RT-AM-014 | **VALIDÉ (2026-11-06)** — `/config/config.yml` ; correction de RT-AM-014 avant E6 (§10.5) |
| A-04 | Clés absentes du contrat : `bot_name`, `lang`, `device_name` | Contrat §12 (schéma sans ces clés) vs code existant qui les utilise | Ajouter une section optionnelle `bot: {display_name, lang, device_name}` avec valeurs par défaut ; mettre à jour le contrat et le mapping Ansible | **VALIDÉ (2026-11-06)** — section `bot.*` optionnelle ; valeurs par défaut à documenter avant implémentation (E6) ; report dans le contrat avant E6 (§10.5) |
| A-05 | Forme `!am user@domaine` (conversion « e-mail ») | Existant vs cdc §13 (parsing strict) | La conserver, via `parse_mxid` | **VALIDÉ (2026-11-06)** — syntaxe `user@domaine` conservée, parsing strict |
| A-06 | Version de Python cible | Non spécifiée (RT-AM-005 ne traite que le CPU) ; poste local en 3.10.12 | `requires-python >=3.10`, CI en 3.10 et 3.12 ; l'image du Lot 4 fixera la version | **VALIDÉ (2026-11-06)** — Python ≥ 3.10 ; CI en 3.10 et 3.12 |
| A-07 | Conserver un script `arn-messager.py` de compatibilité | Aucun déploiement historique à maintenir pour ce fork | Supprimer, point d'entrée `python -m arn_messager` | **VALIDÉ (2026-11-06)** — suppression sans shim en fin de Lot 2 (E16), une fois le nouveau point d'entrée et les tests validés |
| A-08 | Clé de configuration inconnue | RT-AM-019 (TO_VALIDATE) | Échec au démarrage (code 2) | **VALIDÉ (2026-11-06)** — clé inconnue refusée, erreur de configuration explicite, code 2 ; report dans le contrat avant E6 (§10.5) |

### 10.2 Risques et points ouverts

| Point | État | Impact concret sur le Lot 2 |
|---|---|---|
| PF-AM-001 — provenance Git du bot | CONFIRMED (résolu) | Historique présent ; référence vérifiée |
| Branche `lot-2-refactorisation` déjà créée et publiée | CONFIRMED | Aucun ; elle pointe sur `8705fa8`, conformément à A-01 ; synchronisation avec `origin` vérifiée par le propriétaire le 2026-11-06 |
| Divergence `upstream/testing` | Tranché (A-01, 2026-11-06) | Non fusionnée ; consultée comme source d'information uniquement |
| Rejeu des événements au redémarrage (L2-AM-021) | TO_VALIDATE | Correction prévue en E14 ; confirmation par I-4 |
| Comportement de `sync_forever` sur token révoqué avec `nio` 0.25+ | TO_VALIDATE | Détermine l'implémentation d'E13 ; confirmation par I-3 |
| Changement d'API `nio` 0.20 → 0.25/0.26 | TO_VALIDATE | Masqué par les mocks ; I-1 obligatoire avant la sortie |
| Sérialisation des callbacks `nio` (L2-AM-013) | CONFIRMED (limite connue) | Pas de parallélisation au Lot 2 ; documenté |
| Compatibilité des commandes Mautrix (PF-AM-007) | OUT_OF_SCOPE Lot 2 (Lot 3) | Chaînes centralisées sans modification ; bridges en `latest` dans le rôle, à épingler avant les tests |
| Niveaux de pouvoir (PF-AM-006) | OUT_OF_SCOPE Lot 2 (Lot 3) | Niveau paramétré, valeur 100 inchangée |
| PF-AM-013 — antichambre non chiffrée, absente du cdc | OUT_OF_SCOPE Lot 2 (Lot 3) | Seul le refus des salons chiffrés est fait en E15 |
| PostgreSQL, migrations | OUT_OF_SCOPE | Section `postgresql` validée mais inutilisée |
| Dockerfile, non-root, healthcheck | OUT_OF_SCOPE (Lot 4) | Objet d'état préparé en E14 |
| Serveur Synapse de test local non disponible | TO_VALIDATE | Sans lui, S-10 ne peut pas être satisfait ; le Lot 2 ne peut alors pas être déclaré terminé |
| Codes de sortie (RT-AM-013) | Validé côté plan (2026-11-06, §10.4) ; contrat encore TO_VALIDATE | Codes 0/1/2/3 à reporter dans le contrat avant E6 (§10.5) |
| Incohérences documentaires (fichiers nommés v3, contenu v4 ; « cdc v2 » sans numéro dans le cdc) | TO_VALIDATE | Aucun impact technique ; à corriger lors de la prochaine révision des documents |

Aucun point n'est `BLOCKING` au sens d'un empêchement technique. Les
arbitrages étant validés, seule l'harmonisation du contrat runtime (§10.5)
conditionne encore le démarrage d'E6.

### 10.3 Orientations P1 à P5

Acceptées par le propriétaire le 2026-11-06 comme **travaux de
vérification**. Elles ne sont pas toutes considérées comme techniquement
résolues ; chacune est close par les étapes et tests indiqués. (Les
identifiants P1 à P5 désignent ici des orientations et ne se confondent pas
avec les priorités P0 à P3 des constats du §4.)

| ID | Orientation | Rattachement dans ce plan | État |
|---|---|---|---|
| P1 | Harmonisation du contrat runtime | §10.5 ; S-12 | Acceptée — à réaliser avant E6 |
| P2 | Session Matrix persistante dans `/data/session/` | E13 ; I-1, I-2, I-3 ; S-08 | Acceptée — non résolue |
| P3 | Anti-rejeu des événements au redémarrage | L2-AM-021 ; E14 ; I-4 | Acceptée — non résolue |
| P4 | Salons chiffrés : aucune commande traitée | L2-AM-024 ; E15 ; I-6 | Acceptée — non résolue ; la notification de refus reste à trancher (voir E15) |
| P5 | Tests d'intégration sur Synapse jetable | §7.6 (I-1 à I-9) ; S-10 | Acceptée — non résolue, aucun Synapse jetable disponible à ce jour |

### 10.4 Codes de sortie

Confirmés par le propriétaire le 2026-11-06 :

| Code | Signification |
|---|---|
| 0 | Arrêt normal (y compris sur `SIGTERM`/`SIGINT`) |
| 1 | Erreur inattendue |
| 2 | Configuration invalide (dont clé inconnue, A-08) |
| 3 | Échec d'authentification (après la réauthentification unique) |

Implémentation en E14 ; vérification par les tests CLI, I-3, I-7 et I-8.

### 10.5 Harmonisation du contrat runtime avant E6

Le contrat runtime (`../CONTRACT-ARN-MESSAGER-RUNTIME-ANSIBLE-v3.md`) doit
être harmonisé **avant le démarrage d'E6**, et non en fin de lot, pour
refléter :

- A-03 : `/config/config.yml` (correction de RT-AM-014, qui propose
  `/data/config.yml`) ;
- A-04 : section optionnelle `bot.*` et ses valeurs par défaut ;
- A-08 : refus des clés inconnues (RT-AM-019) ;
- §10.4 : codes de sortie 0/1/2/3 (RT-AM-013).

Le contrat est un document commun : ses modifications sont proposées
séparément et nécessitent la validation explicite du propriétaire.

---

## 11. Verdict final

**GO LOT 2 SOUS CONDITIONS**

Justification :

- Le dépôt réel correspond exactement à la référence auditée (`8705fa8`), avec
  son historique. Le code est petit (462 lignes, un seul fichier) et tous les
  défauts du préflight sont confirmés, localisés et traitables sans
  réécriture ni framework.
- Aucun constat ne révèle d'incompatibilité avec le cahier des charges ou le
  contrat runtime. Les écarts sont additifs ou correctifs.
- Les nouveaux constats (rejeu au redémarrage, réécriture de la configuration
  avec le token, préfixes en dur, résolveur DNS en dur, `.gitignore`) élargissent
  le lot sans en changer la nature.
- La divergence avec `upstream/testing` a été tranchée par A-01 (base
  `8705fa8`, sans fusion).

Conditions levées le 2026-11-06 (E0) : A-01 à A-08 validés, codes de sortie
confirmés, orientations P1 à P5 acceptées.

Conditions restantes, dans l'ordre :

1. Avant E1 : disposer d'un environnement de test isolé avec Python 3.10 et
   3.12 (A-06), sur autorisation du propriétaire.
2. Avant E6 : harmoniser le contrat runtime (§10.5) et documenter les valeurs
   par défaut de `bot.*` (A-04).
3. Avant E15 : trancher la notification de refus dans les salons chiffrés
   (P4).
4. Avant la déclaration de fin du lot : disposer d'un Synapse local jetable
   pour les tests I-1 à I-9 (S-10, P5).
