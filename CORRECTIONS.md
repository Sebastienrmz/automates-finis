# Corrections à la reprise

La version reçue contenait deux programmes presque identiques, un environnement Python complet et les réglages de l’éditeur. La version avec choix interactifs a servi de base. Les algorithmes du projet ont été conservés ; les deux copies sont regroupées dans `automates.py` et `main.py`.

- Retrait de `.venv`, des caches et de `.idea` du dépôt. L’archive originale reste inchangée.
- Rangement des exemples dans `data` et résolution de leurs chemins depuis le programme.
- Correction du plantage de l’affichage sur l’alphabet vide (`01.txt`).
- Vérification des nombres déclarés, des états numériques, des symboles et des lignes de transitions.
- Correction de la lecture compacte des états à plusieurs chiffres et prise en charge d’un éventuel marqueur UTF-8 BOM.
- Prise en compte des transitions epsilon entrantes dans la vérification de standardisation.
- Un automate sans état initial n’est plus considéré comme déterministe.
- Retrait des états inaccessibles avant la minimisation.
- Vérification des conditions nécessaires à la complétion, à la minimisation et au complémentaire.
- Arrêt propre à la fermeture de l’entrée ou avec Ctrl+C.
- Ajout des tests, des instructions et d’un paquet Windows utilisable sans Python.
