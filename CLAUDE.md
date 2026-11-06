# ARN-Messager — instructions du dépôt Python

Lire d'abord `../CLAUDE.md` si présent, puis `docs/PLAN-LOT-2-REFACTORISATION.md` et les trois documents communs cités par ce plan. Si les fichiers parents sont absents (clone autonome), demander les documents nécessaires avant toute décision architecturale.

## Lot en cours
Branche `lot-2-refactorisation`, base validée `8705fa8`. Ne pas fusionner `upstream/testing` ; ses changements peuvent être étudiés individuellement. Étape E0 : arbitrages approuvés, à consigner formellement ; démarrer ensuite E1 et suivre E1→E17 dans l'ordre, avec validation humaine à chaque étape.

## Arbitrages validés A-01 à A-08
- A-01 : conserver la base `8705fa8`.
- A-02 : conserver et caractériser les commandes historiques pendant le Lot 2.
- A-03 : utiliser `/config/config.yml`.
- A-04 : ajouter une section de configuration `bot.*` optionnelle ; documenter les valeurs par défaut avant implémentation.
- A-05 : conserver la syntaxe `user@domaine` avec parsing strict.
- A-06 : Python >=3.10 ; CI Python 3.10 et 3.12.
- A-07 : supprimer `arn-messager.py` à la fin du Lot 2, une fois le nouveau point d'entrée et les tests validés.
- A-08 : rejeter les clés YAML inconnues ; erreur de configuration explicite (sortie 2).

## Frontières du Lot 2
Refactoriser, sécuriser et tester le comportement historique ; ne pas implémenter les codes de revendication, antichambres, migrations PostgreSQL, droits du propriétaire à 50, image Docker, déploiement Ansible ou pilote. Préparer les interfaces nécessaires sans activer de comportement du Lot 3.

Conserver les secrets hors YAML et des logs. Authentification non interactive, réutilisation du token vérifié, réauthentification bornée, gestion du SIGTERM et absence de rejeu d'événements. Dépendances E2EE exclues du Lot 2 ; aucune commande traitée dans un salon chiffré. Ne pas supposer que le bot peut expliquer son refus dans un salon chiffré sans test réel.

## Exécution et validation
- Lire les critères exacts de chaque étape E1–E17 dans le plan ; ne pas anticiper une étape ultérieure.
- D'abord tests de caractérisation, puis changements contrôlés ; distinguer comportements historiques et défauts de sécurité à corriger explicitement.
- Exécuter les tests prévus, conserver les résultats et indiquer les tests non exécutés.
- Ne pas déclarer le Lot 2 terminé avant les tests d'intégration sur Synapse jetable prévus au plan.

## Documentation à harmoniser
Avant E6 : corriger la contradiction du contrat runtime entre `/data/config.yml` (RT-AM-014 proposé) et `/config/config.yml` (décision validée), préciser `bot.*`, les clés inconnues et les codes de sortie. Les modifications des documents communs nécessitent une validation explicite.

## Gouvernance Git du dépôt

La section « Gouvernance Git » de `../CLAUDE.md` s'applique intégralement à ce dépôt. Si ce fichier parent est absent (clone autonome), demander ces règles au propriétaire avant toute opération Git autre qu'une consultation ; en tout état de cause, Claude ne crée jamais de commit.
