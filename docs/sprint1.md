# Sprint 1 - Initialisation et Simulation Industrielle

## Objectif

L'objectif du Sprint 1 est de préparer l'architecture du projet NoBreach OT-IoT Sentinel et de développer une première simulation industrielle logicielle basée sur Modbus TCP.

## Technologies utilisées

- Python
- pymodbus
- Git / GitHub
- VS Code
- YAML
- Markdown

## Travail réalisé

- Création de la structure du projet
- Création d'un serveur Modbus TCP simulé
- Création d'un client Modbus TCP simulé
- Simulation des valeurs industrielles :
  - Température
  - Pression
  - Vibration
  - État moteur
  - État panne
  - État production
- Création d'un scénario normal

## Registres Modbus utilisés

| Registre | Adresse Python | Description |
|---|---:|---|
| 40001 | 0 | Température |
| 40002 | 1 | Pression |
| 40003 | 2 | Vibration |
| 40004 | 3 | État moteur |
| 40005 | 4 | État panne |
| 40006 | 5 | État production |

## Résultat attendu

Le serveur Modbus TCP démarre localement sur le port 5020.  
Le client se connecte au serveur et lit les valeurs industrielles simulées en temps réel.