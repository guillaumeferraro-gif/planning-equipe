# Planning IDE — SMUR et TIIH

[Ouvrir le planning dans le navigateur](https://guillaumeferraro-gif.github.io/planning-equipe/Planning-IDE.html)

## Faire un premier essai

1. Ouvrez le planning, puis cliquez sur **Essayer avec une équipe fictive**.
2. Choisissez un mois et cliquez sur **Générer une proposition**.
3. Examinez les gardes et les alertes, puis cliquez sur **Conserver la proposition** si elle vous convient. Un clic sur une case permet de modifier une affectation.

Pour utiliser le planning hors ligne, [ouvrez le fichier HTML sur GitHub](./Planning-IDE.html), cliquez sur **Download raw file** (flèche vers le bas), puis double-cliquez sur le fichier téléchargé. Le navigateur conserve les données sur cet appareil. Exportez une sauvegarde JSON avant de changer de poste ou de navigateur, ou de déplacer le fichier HTML.

## Google Sheets

Pour travailler à plusieurs sur le même planning, ouvrez-le depuis un classeur Google Sheets privé. Son propriétaire installe le script une seule fois.

1. Dans un classeur dédié au planning, ouvrez **Extensions → Apps Script**. Dans **Code.gs**, collez le contenu du [script PlanningGoogle.gs](./google/PlanningGoogle.gs), puis enregistrez le projet.
2. Rechargez le classeur. Le menu **Planning IDE** apparaît en haut de la feuille. Si le menu tarde à apparaître, sélectionnez la fonction **onOpen** dans l’éditeur Apps Script, cliquez sur **Exécuter**, puis revenez au classeur.
3. Dans **Planning IDE → Ouvrir le planning**, suivez la demande d’autorisation Google au premier lancement. Depuis **Partager**, accordez un accès **Éditeur** aux collègues qui doivent travailler sur le planning et conservez l’accès général **Limité**. Chaque collègue ouvre le même classeur et utilise ce menu.

Pour reprendre le planning déjà présent sur votre ordinateur, ouvrez la version locale et choisissez **Imports et exports → Télécharger une sauvegarde JSON**. Dans le classeur, ouvrez **Imports et exports → Restaurer une sauvegarde complète**. Examinez le fichier et confirmez **Remplacer les données** si vous souhaitez qu’il devienne le planning de l’équipe. La version ouverte directement sur GitHub Pages garde sa propre copie sur l’appareil.

Après une modification dans le classeur, attendez **Enregistré dans Google Sheets** avant de fermer la fenêtre. Si deux personnes enregistrent en même temps, celle qui reçoit **Conflit d’enregistrement** peut choisir **Exporter mon brouillon JSON**, puis **Recharger la version partagée** et y reprendre ses changements.

L’onglet **Planning** du classeur présente une vue du planning enregistré. Pour modifier une garde, passez par **Planning IDE → Ouvrir le planning**. Le même menu propose **Actualiser la vue du classeur** et **Restaurer la sauvegarde précédente…**. Cette dernière commande demande confirmation avant de rétablir la version précédente pour toute l’équipe.

## Règles de l’équipe dans la version navigateur

- L’équipe démarre avec sept IDE à **100 %**. Dans **Équipe et règles**, vous pouvez adapter l’effectif, les quotités et l’objectif annuel de temps de travail. Pour mettre à jour une équipe existante, cliquez sur **Mettre toute l’équipe à 100 %**, puis sur **Enregistrer l’équipe**. L’OAT 2026 est de **1 560 h par ETP**, du 1ᵉʳ janvier au 31 décembre.
- Le SMUR fonctionne chaque jour avec une IDE de **8 h à 20 h** et une IDE de **20 h à 8 h le lendemain**. Le TIIH fonctionne **le mardi, le jeudi et le vendredi**, hors jours fériés. Il commence à **9 h** et dure normalement **7 h 42**, soit une fin à **16 h 42**.
- Deux plafonds s’appliquent au travail effectif de chaque IDE. Le maximum est de **48 h sur sept jours glissants** et de **44 h par semaine du lundi au dimanche**. Le repos minimum entre deux postes est de **12 h** selon les horaires affichés.
- Après **trois dates consécutives de prise de poste**, les **deux jours suivants** sont obligatoirement sans nouvelle prise de poste. Une série du vendredi au dimanche impose donc le repos le lundi et le mardi. Le repos peut durer plus longtemps. Le générateur cherche aussi à éviter les journées et les nuits travaillées isolément.
- Le week-end de nuit réunit les nuits de **vendredi, samedi et dimanche**. Le week-end de jour réunit **samedi et dimanche** et le générateur cherche à inclure le vendredi. Une IDE qui travaille le week-end bénéficie d’un repos de jour le lundi suivant.
- Une période de nuit dure **14 à 21 jours calendaires**, repos compris. Le générateur tient compte de l’historique pour répartir les gardes de jour et de nuit entre les IDE.
- Une absence est créditée de **7 h 42** par jour du lundi au vendredi. Un créneau individuel peut avoir une durée différente.

## Gérer une arrivée, un départ ou une quotité temporaire

Dans **Équipe et règles**, ouvrez **Effectif**, puis **Ajouter un agent**. Indiquez le nom, la date d’entrée et la quotité de base. Pour un départ, choisissez **Retirer un agent**, l’IDE et son dernier jour dans l’équipe. Les deux dates sont incluses. **Examiner le retrait** présente les postes en brouillon à réattribuer avant confirmation. S’il reste des postes confirmés ou verrouillés après le départ, l’application demande de les revoir. Les plannings et compteurs antérieurs restent consultables.

Dans **Quotités temporaires**, cliquez sur **Ajouter une période** et choisissez l’IDE, le pourcentage et les dates de début et de fin incluses. Par exemple, une IDE dont la quotité de base est de 100 % peut passer à 80 % du 1ᵉʳ au 30 juin. Le 1ᵉʳ juillet, l’application reprend automatiquement la quotité de base applicable à cette date. Pour transférer les contrats et ces périodes sur un autre appareil, utilisez la sauvegarde JSON complète. Le CSV mensuel sert à transférer les postes.

## Adapter un ou plusieurs postes de TIIH

Pour un seul poste, ouvrez **TIIH → Un poste**, puis cliquez sur **Modifier** sur la ligne du poste concerné. Dans **Adapter une journée**, choisissez l’action voulue, puis **Appliquer au TIIH**.

- **Modifier la durée** conserve la date du poste. Saisissez la durée en heures et minutes, de `0:01` à `48:00`. Si le poste dépasse minuit, l’heure de fin précise le jour de sortie. Par exemple, `5:30` donne un TIIH de **9 h à 14 h 30**. **Rétablir la durée de 7 h 42** ramène ce poste à son horaire habituel.
- **Supprimer** retire uniquement ce TIIH du planning. **Déplacer** le reporte à une autre date avec sa durée. **Restaurer** le remet à sa date d’origine avec la durée mémorisée.

Pour appliquer l’une de ces cinq actions à plusieurs dates, ouvrez **TIIH → Plusieurs postes**.

1. Cochez les postes voulus ou cliquez sur **Sélectionner le mois affiché**. Pour choisir, par exemple, les jeudis de décembre, ouvrez **Sélectionner par période**, indiquez les dates de début et de fin incluses, cochez uniquement **Jeudi**, puis cliquez sur **Ajouter une période**. Vous pouvez changer de mois pour compléter la sélection. **Vider la sélection** permet de recommencer.
2. Choisissez l’action. Pour **Déplacer**, indiquez un décalage en jours par rapport à la date d’origine de chaque poste. Un décalage de `+1` place ainsi les TIIH du mardi le mercredi suivant.
3. Cliquez sur **Examiner les changements**. Le tableau affiche l’avant et l’après pour chaque poste, ainsi que les affectations à réattribuer. Cliquez sur **Appliquer les changements** pour valider la sélection.

La durée du poste compte dans le temps de travail de l’IDE affectée. Le CSV mensuel reprend la durée des TIIH affectés, par exemple `TIIH (5:30)`. Pour conserver les suppressions, déplacements et durées personnalisées lors d’un changement d’appareil, emportez la **sauvegarde JSON complète** depuis **Imports et exports**.

## Corriger les affectations d’une seule journée

Dans **Planning**, cliquez sur **Modifier une journée** ou sur la date en tête de la grille d’équipe. Choisissez les IDE pour le SMUR J, le SMUR N et, si le poste est ouvert, le TIIH. Un poste ouvert sans titulaire apparaît comme **À pourvoir**. Pour conserver votre choix lors d’une prochaine génération, cochez **Verrouiller les cases modifiées pour les prochains calculs**. Cliquez sur **Enregistrer cette journée**. Cette correction porte uniquement sur les affectations de cette date. Pour modifier une seule case, cliquez directement sur celle de l’IDE concernée.

Pour préparer un mois complet, utilisez **Générer une proposition**. Par défaut, **Conserver la proposition** enregistre uniquement le mois affiché. Si vous voulez également enregistrer les affectations proposées au-delà du dernier jour, cochez **Inclure l’anticipation après ce mois** avant de générer la proposition.

## Importer un historique ou exporter le planning

Dans **Imports et exports**, choisissez **Ajouter un historique mensuel** pour reprendre les anciens fichiers `planning_AAAA_MM.json` ou un CSV mensuel exporté par cette application. Associez les noms aux IDE de votre équipe et examinez les affectations avant de les reprendre. À la confirmation de l’import, vous pouvez choisir la date de passage de toute l’équipe à 100 %. Laissez le champ vide pour conserver les quotités existantes. Les postes de l’historique connu servent à équilibrer les prochaines propositions. Dans **Planning**, consultez **Répartition des postes par IDE** pour comparer les gardes. Une sauvegarde JSON complète de Planning IDE restaure aussi l’équipe, les absences et les paramètres sur un autre appareil.

Dans **Planning**, la vue **Équipe** s’ouvre sur **Mois entier**. Les boutons **1–7**, **8–14**, etc. affichent une semaine. Choisissez **Par IDE** puis **IDE affichée** pour consulter les postes du mois d’une personne. Le signe **?** indique une date non renseignée et le tiret **—** un repos connu. Les deux vues présentent aussi la proposition avant validation. Vous pouvez exporter le mois complet en CSV ou utiliser **Exporter le mois de cette IDE en CSV** dans la vue individuelle. Dans **Compteurs**, vous pouvez aussi exporter le suivi annuel de chaque IDE.

Pour télécharger le planning en **PDF**, choisissez le mois et la vue voulue, puis cliquez sur **Exporter en PDF** au-dessus du tableau. En vue **Équipe**, le PDF contient la grille mensuelle de toute l’équipe. En vue **Par IDE**, choisissez d’abord la personne dans **IDE affichée** pour obtenir ses dates, ses postes et ses horaires. Le PDF couvre toujours le mois complet, même si une seule semaine est affichée à l’écran.

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
