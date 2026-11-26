# Planning IDE — SMUR et TIIH

[Ouvrir le planning dans le navigateur](https://guillaumeferraro-gif.github.io/planning-equipe/Planning-IDE.html)

## Faire un premier essai

1. Ouvrez le planning, puis cliquez sur **Essayer avec une équipe fictive**.
2. Choisissez un mois et cliquez sur **Générer une proposition**.
3. Examinez les gardes et les alertes, puis cliquez sur **Conserver la proposition** si elle vous convient. Un clic sur une case permet de modifier une affectation.

Pour utiliser le planning hors ligne, [ouvrez le fichier HTML sur GitHub](./Planning-IDE.html), cliquez sur **Download raw file** (flèche vers le bas), puis double-cliquez sur le fichier téléchargé. Le navigateur conserve les données sur cet appareil. Exportez une sauvegarde JSON avant de changer de poste ou de navigateur, ou de déplacer le fichier HTML.

## Règles de l’équipe dans la version navigateur

- L’équipe comprend sept IDE à **100 %** par défaut. Dans **Équipe et règles**, vous pouvez modifier les quotités et l’objectif annuel de temps de travail. Pour mettre à jour une équipe existante, cliquez sur **Mettre toute l’équipe à 100 %**, puis sur **Enregistrer l’équipe**. L’OAT 2026 est de **1 560 h par ETP**, du 1ᵉʳ janvier au 31 décembre.
- Le SMUR fonctionne chaque jour avec une IDE de 8 h à 20 h et une IDE de 20 h à 8 h le lendemain. Le TIIH fonctionne **le mardi et le vendredi**, de 9 h à 16 h 42, hors jours fériés. Dans **TIIH**, une occurrence peut être supprimée, déplacée ou rétablie.
- Deux plafonds s’appliquent au travail effectif de chaque IDE. Le maximum est de **48 h sur sept jours glissants** et de **44 h par semaine du lundi au dimanche**. Le repos minimum entre deux postes est de **12 h** selon les horaires affichés.
- Une série comprend au plus **trois prises de poste consécutives**. Le générateur cherche à éviter les journées ou nuits isolées et vise **au plus deux jours de repos entre deux séries**. Il signale les écarts pour que vous puissiez examiner le planning proposé.
- Le week-end de nuit réunit les nuits de **vendredi, samedi et dimanche**. Le week-end de jour réunit **samedi et dimanche** et le générateur cherche à inclure le vendredi. Une IDE qui travaille le week-end bénéficie d’un repos de jour le lundi suivant.
- Une période de nuit dure **14 à 21 jours calendaires**, repos compris. Le générateur tient compte de l’historique pour répartir les gardes de jour et de nuit entre les IDE.
- Une absence est créditée de **7 h 42** par jour du lundi au vendredi. Un créneau individuel peut avoir une durée différente.

## Importer un historique ou exporter le planning

Dans **Imports et exports**, choisissez **Ajouter un historique mensuel** pour reprendre les anciens fichiers `planning_AAAA_MM.json` ou un CSV mensuel exporté par cette application. Associez les noms aux IDE de votre équipe et examinez les affectations avant de les reprendre. À la confirmation de l’import, vous pouvez choisir la date de passage de toute l’équipe à 100 %. Laissez le champ vide pour conserver les quotités existantes. Les postes de l’historique connu servent à équilibrer les prochaines propositions. Dans **Planning**, consultez **Répartition des postes par IDE** pour comparer les gardes. Une sauvegarde JSON complète de Planning IDE restaure aussi l’équipe, les absences et les paramètres sur un autre appareil.

Dans **Planning**, la vue **Équipe** s’ouvre sur **Mois entier**. Les boutons **1–7**, **8–14**, etc. affichent une semaine. Choisissez **Par IDE** puis **IDE affichée** pour consulter les postes du mois d’une personne. Le signe **?** indique une date non renseignée et le tiret **—** un repos connu. Les deux vues présentent aussi la proposition avant validation. Vous pouvez exporter le mois complet en CSV ou utiliser **Exporter le mois de cette IDE en CSV** dans la vue individuelle. Dans **Compteurs**, vous pouvez aussi exporter le suivi annuel de chaque IDE.

## Ancienne version Python

Les sections suivantes décrivent l’application Streamlit et ses règles historiques.

### Fonctionnalités

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

### Lancer sous Windows

Installer Python 3.11 ou plus récent (Python 3.12 conseillé).

1. Télécharger le dépôt avec **Code → Download ZIP**, puis extraire toute l'archive.
2. Double-cliquer sur **demarrer_windows.bat**.
3. Ouvrir **http://localhost:8501** dans le navigateur.

Le premier lancement télécharge les dépendances. Garder la fenêtre de lancement ouverte
pendant l'utilisation.

### Lancer sous macOS ou Linux

Depuis le dossier du projet :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Ouvrir http://localhost:8501. L'application écoute sur l'ordinateur local ; publier le
code sur GitHub ne met pas le planning en ligne.

### Premier essai

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

### Règles de calcul

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

### Données et reprise de l'existant

Les fichiers sont conservés dans **data/** et exclus de Git. La variable
**PLANNING_DATA_DIR** permet de choisir un autre dossier persistant.

Dans **Données**, télécharger une sauvegarde JSON ou importer les anciens fichiers
**planning_année_mois.json** présents dans le dossier de données. Les sources sont conservées ;
les plannings importés restent des brouillons à contrôler.

La sauvegarde utilise un remplacement atomique, une copie de secours
**planning-state.backup.json** et une vérification de révision pour éviter les écrasements
entre sessions. Cette version est destinée à un responsable utilisant l'application localement.

### Vérification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

19 tests automatisés vérifient les règles métier, le moteur, la persistance et les
parcours Streamlit. La version HTML a également été testée hors ligne dans Chromium.

Le [cahier des charges](specs/001-fiabiliser-planning-ide/spec.md) détaille le cadrage.
