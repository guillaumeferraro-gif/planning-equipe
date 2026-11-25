# Planning IDE — SMUR et TIIH

Application locale de planning d'équipe infirmière, avec génération automatique et
modifications manuelles.

## Ouvrir le planning sans installer Python

1. Ouvrez [Planning-IDE.html](./Planning-IDE.html) sur GitHub, puis cliquez sur **Download raw file** (flèche vers le bas) pour télécharger le fichier.
2. Double-cliquez sur le fichier téléchargé. Le planning s’ouvre dans votre navigateur et fonctionne hors ligne.
3. Cliquez sur **Essayer avec une équipe fictive**, puis sur **Générer une proposition**. Examinez le mois proposé avant de le conserver.

Pour préparer le planning de votre équipe, renseignez les quatre quotités manquantes dans les paramètres de l’équipe. Vous pourrez saisir l’OAT quand vous le connaîtrez.

Le navigateur conserve les données sur cet ordinateur. Exportez une sauvegarde JSON avant de changer de navigateur ou de poste, de déplacer le fichier ou d’effacer les données de navigation.

## Fonctionnalités

- SMUR J de 8 h à 20 h et SMUR N de 20 h à 8 h le lendemain, chaque jour.
- TIIH de 9 h à 16 h 42 les mardis, jeudis et vendredis non fériés :
  suppression, déplacement ou restauration d'une occurrence.
- Quotités individuelles modifiables et datées ; objectif annuel de travail (OAT)
  facultatif, sur l'année civile.
- Absences par période ou créneau ; crédit par défaut de 7 h 42 du lundi au vendredi,
  avec durées personnalisables.
- Périodes jour/nuit proches de quinze jours ; nuits isolées autorisées et pénalisées.
- Contrôles de repos, séries, couverture, absences et frontières entre mois.
- Sauvegardes locales, export CSV, import des anciens plannings et sauvegarde JSON.

## Lancer la version Python sous Windows

Installer Python 3.11 ou plus récent (Python 3.12 conseillé).

1. Télécharger le dépôt avec **Code → Download ZIP**, puis extraire toute l'archive.
2. Double-cliquer sur **demarrer_windows.bat**.
3. Ouvrir **http://localhost:8501** dans le navigateur.

Le premier lancement télécharge les dépendances. Garder la fenêtre de lancement ouverte
pendant l'utilisation.

## Lancer la version Python sous macOS ou Linux

Depuis le dossier du projet :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Ouvrir http://localhost:8501. L'application écoute sur l'ordinateur local ; publier le
code sur GitHub ne met pas le planning en ligne.

## Premier essai

1. Dans **Équipe et règles**, personnaliser les noms et renseigner les sept quotités.
   Les valeurs inconnues restent vides et bloquent la génération. L'OAT peut rester vide.
2. Dans **Planning**, choisir un mois puis **Générer une proposition**.
3. Examiner le résultat puis choisir **Conserver cette proposition**.
4. Ajouter une absence du vendredi au lundi : indisponibilité sur quatre jours,
   crédit par défaut de **15 h 24**.
5. Supprimer ou déplacer un poste TIIH, puis recalculer le planning.

La génération conserve les affectations verrouillées et les postes confirmés réalisés.
Elle inclut environ trois semaines d'anticipation, visibles avant acceptation.
Un historique absent est signalé comme incomplet : il n'est pas assimilé à un repos connu.

## Règles de calcul

- Repos : 12 h sur les **horaires affichés**, selon la convention choisie.
- Travail effectif : maximum 48 h sur toute fenêtre de 168 h réelles.
- Maximum trois dates consécutives de prise de poste.
- Samedi et dimanche travaillés ensemble au même poste ; aucune nouvelle prise
  de poste le lundi suivant.
- Régimes initialement réglés sur 14 à 16 jours, cible 15, paramètres modifiables.
- SMUR J/N crédités 12 h ; TIIH crédité 7 h 42 ; une nuit est rattachée à sa date de début.
- Absences créditées séparément du travail effectif. Le crédit personnalisé d'un
  créneau est saisi explicitement.
- Les compteurs distinguent confirmé, planifié non confirmé et absences.
  Une cible annuelle exige l'OAT et des quotités connues sur toute l'année.

Une limite de temps de recherche n'est pas une preuve d'impossibilité. Le programme
distingue les différents résultats et contrôle les propositions indépendamment du moteur.

## Données et reprise de l'existant (version Python)

Les fichiers sont conservés dans **data/** et exclus de Git. La variable
**PLANNING_DATA_DIR** permet de choisir un autre dossier persistant.

Dans **Données**, télécharger une sauvegarde JSON ou importer les anciens fichiers
**planning_année_mois.json** présents dans le dossier de données. Les sources sont conservées ;
les plannings importés restent des brouillons à contrôler.

La sauvegarde utilise un remplacement atomique, une copie de secours
**planning-state.backup.json** et une vérification de révision pour éviter les écrasements
entre sessions. Cette version est destinée à un responsable utilisant l'application localement.

## Vérification (version Python)

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

19 tests automatisés vérifient les règles métier, le moteur, la persistance et les
parcours Streamlit. La version HTML a également été testée hors ligne dans Chromium.

Le [cahier des charges](specs/001-fiabiliser-planning-ide/spec.md) détaille le cadrage.
