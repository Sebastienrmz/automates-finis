# Traitement d’automates finis

Projet de cours EFREI P2, **2025–2026**, réalisé en **équipe de trois**. Le programme lit un automate dans un fichier texte, affiche sa table de transitions et permet d’appliquer les transformations étudiées en cours.

Le programme fonctionne en console avec la bibliothèque standard de Python.

## Essayer rapidement sur Windows

1. Ouvrir [la dernière version](https://github.com/Sebastienrmz/automates-finis/releases/latest).
2. Télécharger **Automates-finis-Windows.zip**.
3. Extraire tout le ZIP dans un dossier.
4. Ouvrir **Tester.bat**. Python n’est pas nécessaire pour cette version.

Garder ensemble l’exécutable, le dossier `_internal` et le dossier `data`. Il ne faut pas lancer le programme directement depuis le ZIP.

### Premier essai

- Saisir **exemple** dans le menu.
- Répondre **o** si le programme propose de standardiser l’automate.
- Répondre **o** pour poursuivre la déterminisation et la minimisation.
- Tester **abaa** : le mot doit être accepté. Tester **aba** : il doit être refusé.
- Saisir **fin** pour terminer la reconnaissance, puis choisir **1** ou **2** pour afficher le complémentaire.
- Répondre **n** pour quitter.

Une ligne vide à l’étape de reconnaissance représente le mot vide. Les mots reconnus sont des suites de lettres de l’alphabet du fichier. Le complémentaire est défini par rapport à ce même alphabet.

## Fonctions du programme

- Lecture de fichiers texte et affichage de la table de transitions.
- Vérification des propriétés : standard, déterministe et complet.
- Standardisation avec création d’un nouvel état initial.
- Déterminisation par construction des sous-ensembles, avec fermeture epsilon.
- Complétion avec ajout d’un état puits si nécessaire.
- Minimisation par raffinement de partitions, après retrait des états inaccessibles.
- Reconnaissance de mots et construction du langage complémentaire.

Le menu permet de choisir les transformations à appliquer. Les résultats sont affichés sous forme de tables et de correspondances entre états.

## Lancer le code

Prérequis : **Python 3.10 ou plus récent**. Ouvrir un terminal dans le dossier contenant `main.py` :

```sh
python main.py
```

Sous Windows, `py -3 main.py` peut aussi être utilisé. Aucun `pip install` n’est nécessaire.

Pour traiter directement un fichier :

```sh
python main.py data/exemple.txt
```

Le menu retrouve les exemples livrés indépendamment du dossier depuis lequel le programme est lancé. Un chemin passé en argument est interprété par rapport au dossier courant du terminal.

## Format d’un fichier

```text
2
3
1 0
1 2
2
0 a 1
1 b 2
```

Cet exemple définit l’alphabet `{a,b}`, trois états `0,1,2`, l’état initial `0`, l’état terminal `2` et deux transitions. Il reconnaît le mot `ab`.

Les cinq premières lignes indiquent, dans l’ordre :

1. Le nombre de symboles : les lettres sont `a`, `b`, etc., jusqu’à `z`.
2. Le nombre d’états numériques, numérotés de `0` à `n-1`.
3. Le nombre d’états initiaux, suivi de leurs numéros.
4. Le nombre d’états terminaux, suivi de leurs numéros.
5. Le nombre de transitions, suivies chacune d’une ligne `départ symbole arrivée`.

`*` représente une transition epsilon. Les commentaires commençant par `#`, les lignes vides et le format compact `0a1` sont acceptés. Un état nommé en majuscules, par exemple `P`, peut être ajouté lorsqu’il apparaît dans une transition. Les états initiaux et terminaux du fichier restent numériques.

Les **45 fichiers** du dossier `data` comprennent les exemples `01` à `44` et `exemple`. Le premier montre le cas d’un alphabet vide.

## Tests

```sh
python -m unittest discover -s tests -v
```

Les tests vérifient les 45 fichiers, 80 automates générés de manière reproductible et plusieurs fichiers invalides. Ils comparent exactement les langages par exploration des ensembles d’états atteignables : standardisation, déterminisation et minimisation doivent conserver le langage ; le complément doit inverser l’acceptation. Ils vérifient aussi que les états du résultat minimal sont distinguables.

Le workflow GitHub lance ces tests sur Windows et Linux, puis construit et essaie la version Windows avant de la publier.

## Organisation

```text
automates.py          Modèle, lecture et algorithmes
main.py               Menu et déroulement du traitement
data/                 45 exemples texte
tests/                Tests des transformations et de la lecture
tools/                Préparation de la version Windows
```

Les corrections de reprise sont détaillées dans [CORRECTIONS.md](CORRECTIONS.md). Le projet est destiné aux exemples de cours : la déterminisation peut créer beaucoup d’états sur des automates plus volumineux.
