# Planning IDE — SMUR et TIIH

[Ouvrir le planning dans le navigateur](https://guillaumeferraro-gif.github.io/planning-equipe/Planning-IDE.html)

## Faire un premier essai

1. Ouvrez le planning, puis cliquez sur **Essayer avec une équipe fictive**.
2. Choisissez un mois et cliquez sur **Générer une proposition**.
3. Examinez les gardes et les alertes, puis cliquez sur **Conserver la proposition** ou **Conserver le brouillon** selon le résultat. Un clic sur une case permet de modifier une affectation.

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
- Le générateur compte le travail effectif sur **168 heures glissantes**, y compris aux changements de mois ou d’année. Dès que la fenêtre comprend un SMUR J ou un TIIH, le total de tous les postes, nuits comprises, est limité à **48 h**. Si elle ne contient que des SMUR N, un dépassement de 48 h déclenche un avertissement et la proposition peut être conservée. Le repos minimum entre deux postes est de **12 h** selon les horaires affichés.
- Après **trois dates consécutives de prise de poste**, les **deux jours suivants** sont des repos. Seul le roulement à deux IDE prévoit une reprise le mardi soir pour l’IDE B après les trois nuits du premier week-end. Le générateur cherche aussi à éviter les journées et les nuits travaillées isolément.
- Le week-end de jour réunit **samedi et dimanche** et le générateur cherche à inclure le vendredi. Une IDE qui travaille le week-end bénéficie d’un repos de jour le lundi suivant.
- Une même IDE ne peut pas travailler **deux week-ends complets consécutifs**. Un week-end est complet si elle prend un poste le vendredi, le samedi **et** le dimanche. SMUR J, SMUR N et TIIH comptent, même si le poste change d’un jour à l’autre. Un samedi et un dimanche travaillés sans le vendredi ne forment pas un bloc complet. La règle suit le calendrier à travers les mois et les années. Par exemple, une IDE qui travaille les 25, 26 et 27 décembre 2026 ne peut pas aussi travailler les trois jours du 1ᵉʳ au 3 janvier 2027.
- Une absence est créditée de **7 h 42** par jour du lundi au vendredi. Un créneau individuel peut avoir une durée différente.

### Répartir les nuits SMUR

Le roulement par défaut, **Trois IDE avec relève**, répartit les quatorze nuits entre deux titulaires (IDE A et B) et une relève (IDE C). Chaque garde commence à 20 h à la date indiquée.

| Semaine de la trame | Lundi | Mardi | Mercredi | Jeudi | Vendredi | Samedi | Dimanche |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Première semaine | B | A | A | A | B | B | B |
| Deuxième semaine | A | C | C | C | A | A | A |

**A assure 7 nuits, B en assure 4 et C en assure 3.** A alterne nuits et repos pendant les deux semaines. B alterne nuits et repos pendant la première semaine. En deuxième semaine, B peut reprendre un SMUR J ou un TIIH dès que sa période de nuit de 14 à 21 jours est terminée et que 48 h de repos se sont écoulées depuis la fin de sa dernière garde de nuit. La relève C peut travailler de jour avant ou après sa propre période de nuit. Les autres règles d’heures et de repos s’appliquent à chaque IDE. À la quinzaine suivante, le calcul fait tourner les rôles en tenant compte des disponibilités et des nuits déjà effectuées.

Dans **Équipe et règles → Roulement de nuit**, le champ **Premier lundi du roulement de nuit** fixe le début de la première semaine. En présence de gardes déjà saisies, vérifiez la date et confirmez le changement. Il peut décaler les quinzaines et réinitialiser leurs choix de relève. Sur une équipe neuve sans date enregistrée, le lundi 4 janvier 2027 sert de repère pour calculer les quinzaines qui précèdent et qui suivent.

Si la relève manque, les nuits concernées restent **à pourvoir**. Le bouton **Essayer avec deux IDE** permet de comparer une proposition. En mode **Deux IDE sans relève**, A et B alternent exclusivement nuits et repos pendant les deux semaines. B reprend les nuits du mardi au jeudi de la deuxième semaine. Les onze autres nuits du tableau gardent le même rôle. Après ses trois nuits du vendredi au dimanche de la première semaine, B se repose le lundi et peut reprendre le mardi à 20 h. Ses six nuits représentent habituellement **72 h sur 168 h**. Le relevé **Heures de nuit sur 168 h** affiche les dates et le pic du dépassement.

Dans la fonction publique hospitalière française, l’article 6 du décret n° 2002-9 fixe en principe une limite de **48 h de travail effectif sur sept jours**, nuits comprises. Faites vérifier par votre établissement toute proposition en dépassement. [Article 6 sur Légifrance](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000051691541).

Une période de nuit dure **14 à 21 jours calendaires**, repos compris. Après la dernière nuit de cette période, il faut **48 heures de repos** avant de reprendre un poste. Par exemple, si la dernière nuit démarre dimanche à 20 h et finit lundi à 8 h, la première reprise possible est mercredi à 8 h, sous réserve des autres règles. Les périodes de jour ont une durée libre. Une IDE peut par exemple rester 28 jours en période de jour, ou davantage.

Pour équilibrer les nuits entre IDE, le générateur compte les **gardes SMUR N** déjà assurées dans l’historique et celles qu’il prépare. Chaque garde de 20 h à 8 h compte pour une nuit. Deux IDE qui ont assuré quatre nuits ont ainsi le même total de nuits, même si leur nombre de gardes de jour ou la durée de leurs périodes diffère. Les compteurs annuels permettent aussi de suivre les heures travaillées et l’OAT.

Dans une proposition, ouvrez **Voir le roulement de nuit** pour consulter le rôle et le nombre de nuits de chaque IDE. Pour essayer un autre mode sur une période déjà planifiée, ouvrez **Compléter le planning existant** et choisissez le **Roulement pour les quinzaines de cette proposition**. Le choix est enregistré pour les quinzaines indiquées lorsque vous conservez la proposition.

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

Pour attribuer à une IDE un poste déjà occupé, ouvrez sa case, sélectionnez le poste, puis vérifiez les deux noms dans l’aperçu. Le bouton **Réattribuer** précise le poste et sa nouvelle titulaire. Lors de l’ajout manuel d’un SMUR J ou d’un TIIH, l’application peut corriger un repère automatique de nuit si cette période ne contient aucune garde de nuit ni aucun repère verrouillé. Les autres dates gardent leurs affectations. Si une contrainte empêche la modification, **Voir les IDE possibles pour…** permet de consulter les autres titulaires possibles pour ce poste.

## Compléter un planning déjà commencé

Dans **Planning**, choisissez le mois puis **Compléter le planning existant**. Le **Premier jour à compléter** proposé est celui où il manque au moins un poste SMUR ou TIIH prévu. Une journée où seule la nuit est attribuée peut donc être complétée dès son poste de jour. Ajustez cette date si besoin. Par exemple, si le début du planning est déjà diffusé jusqu’au dimanche 3 janvier, choisissez le lundi 4 janvier pour poursuivre. Vous pouvez fixer un **Dernier jour à compléter** ou aller jusqu’à la fin du mois.

Le mode **Conserver toutes les gardes saisies**, sélectionné par défaut, complète les postes vacants de l’intervalle. Pour appliquer la nouvelle trame à un mois déjà rempli, choisissez **Recalculer les gardes non protégées sur ces dates**, puis vérifiez le premier et le dernier jour. L’aperçu du recalcul indique combien d’affectations changent ou redeviennent vacantes. Les gardes et repos verrouillés ou confirmés sont protégés dans les deux modes.

Cliquez sur **Préparer la proposition** pour examiner le résultat. Les dates en dehors de l’intervalle sont conservées. Les gardes de décembre comptent pour vérifier les heures et les repos de janvier, ainsi que pour équilibrer les nuits entre IDE.

Lors de la reprise d’un ancien planning, la fenêtre indique à partir de quel lundi s’applique la nouvelle trame. Si les rôles hérités de décembre sont incompatibles avec ceux de la quinzaine en cours, une option datée permet par exemple de **Commencer la nouvelle trame le lundi 4 janv. 2027**. Vérifiez les dates des quinzaines concernées et les choix de relève à redéfinir. Les gardes antérieures comptent toujours pour les heures et les repos. Le nouveau départ prend effet quand vous conservez la proposition.

Par défaut, le calcul cherche d’abord à couvrir les SMUR, puis à réduire les périodes sans garde. Pour essayer une autre répartition, cochez **Priorité aux IDE sans garde depuis sept jours**. Ce choix peut laisser davantage de SMUR J ou N à pourvoir. L’aperçu compare, avant et après le calcul, le nombre de SMUR attribués et le nombre de périodes d’au moins sept jours sans garde. Examinez les dates des postes vacants avant de choisir **Conserver la proposition** ou **Conserver le brouillon**.

### Traiter un planning incomplet

Si le calcul ne trouve pas de solution complète, une **Proposition partielle** permet d’avancer avec les gardes compatibles. Le calcul donne la priorité aux postes obligatoires **SMUR J** et **SMUR N**, puis aux **TIIH** ouverts. Un SMUR encore vacant reste un poste à couvrir.

Consultez **Postes à pourvoir** pour repérer les dates et les horaires sans titulaire. **Conflits à examiner** indique les gardes déjà saisies qui demandent une vérification, par exemple si deux affectations empêchent un repos suffisant. **Heures de nuit sur 168 h** affiche les dépassements liés uniquement aux nuits, même sur un planning entièrement pourvu. Dans la vue par IDE, le relevé porte sur la personne sélectionnée.

Dans **Périodes sans garde inscrite**, repérez les IDE qui cumulent **sept dates consécutives ou plus sans garde**. Le décompte traverse les fins de mois lorsque les journées sont renseignées. Une absence, une date hors effectif ou un repos verrouillé ou confirmé interrompt la série. Le détail précise les dates et signale les cases individuelles inconnues ou les repos prévus par le roulement de nuit. Les périodes figurent aussi à la fin du PDF.

Cliquez sur **Chercher un poste** à côté de la période. La recherche affiche les **Postes à pourvoir**, puis les **Réaffectations possibles** avec le nom de l’IDE qui céderait sa garde. Elle écarte une réaffectation qui créerait ou prolongerait une telle période sans garde pour cette IDE. Sur le planning enregistré, cliquez sur un poste pour examiner le changement avant de le valider. Dans une proposition, conservez d’abord le brouillon ou la proposition pour pouvoir modifier la garde. Si aucun poste ne convient, ouvrez **Voir les empêchements rencontrés**.

Pour reprendre le travail plus tard ou le partager avec l’équipe, cliquez sur **Conserver le brouillon**. Depuis le planning enregistré, ouvrez la journée concernée avec **Modifier**. La liste se met à jour après la correction. Dans l’onglet **Planning** du classeur, les postes vacants d’un mois entamé portent la mention **À pourvoir**. Le PDF d’équipe indique les postes vacants sous les dates correspondantes et détaille les conflits à examiner. Le CSV mensuel garde son format de réimportation.

## Refaire une proposition ou effacer un mois

Pour recalculer un mois avec les règles actuelles, choisissez-le dans **Planning** et cliquez sur **Faire une autre proposition**. Ce bouton est disponible depuis un mois déjà planifié ou une proposition en cours. Pour un mois vierge, commencez par **Générer une proposition**. Vous pouvez examiner plusieurs répartitions avant de cliquer sur **Conserver la proposition**. Si le calcul ne trouve aucune répartition différente des gardes, le planning en place reste disponible. Si des week-ends consécutifs du mois voisin bloquent la génération, l’alerte indique les dates et propose d’ouvrir ce mois. Par défaut, l’enregistrement porte sur le mois affiché. Pour enregistrer aussi les affectations proposées après le dernier jour, cochez **Inclure l’anticipation après ce mois** avant le calcul.

Pour repartir d’un mois vide, choisissez **Effacer le mois…**. L’aperçu indique les affectations du mois concernées pour toute l’équipe. Par défaut, les cases et périodes verrouillées ainsi que les postes confirmés sont protégés. Pour les effacer aussi, cochez **Inclure les cases et les périodes verrouillées** ou **Inclure les postes confirmés**, selon votre besoin. Relisez l’aperçu puis cliquez sur **Confirmer l’effacement**. Les autres mois, l’effectif, les contrats, les absences, les règles et les TIIH prévus sont conservés. Pour revenir sur cette action, cliquez immédiatement sur **Annuler l’effacement**, avant de changer de mois ou de modifier le planning.

## Importer un historique ou exporter le planning

Dans **Imports et exports**, choisissez **Ajouter un historique mensuel** pour reprendre les anciens fichiers `planning_AAAA_MM.json` ou un CSV mensuel exporté par cette application. Associez les noms aux IDE de votre équipe et examinez les affectations avant de les reprendre. À la confirmation de l’import, vous pouvez choisir la date de passage de toute l’équipe à 100 %. Laissez le champ vide pour conserver les quotités existantes. Les postes de l’historique connu servent à équilibrer les prochaines propositions. Dans **Planning**, consultez **Répartition des postes par IDE** pour comparer les gardes. Une sauvegarde JSON complète de Planning IDE restaure aussi l’équipe, les absences et les paramètres sur un autre appareil.

Dans **Planning**, la vue **Équipe** s’ouvre sur **Mois entier**. Les boutons **1–7**, **8–14**, etc. affichent une semaine. Choisissez **Par IDE** puis **IDE affichée** pour consulter les postes du mois d’une personne. Le signe **?** indique une date non renseignée et le tiret **—** un repos connu. Les deux vues présentent aussi la proposition avant validation. Vous pouvez exporter le mois complet en CSV ou utiliser **Exporter le mois de cette IDE en CSV** dans la vue individuelle. Dans **Compteurs**, vous pouvez aussi exporter le suivi annuel de chaque IDE.

Pour télécharger le planning en **PDF**, choisissez le mois et la vue voulue, puis cliquez sur **Exporter en PDF** au-dessus du tableau. Dans Google Sheets, cliquez ensuite sur **Télécharger le PDF** ou sur **Ouvrir le PDF** pour le consulter. En vue **Équipe**, le PDF contient la grille mensuelle de toute l’équipe. En vue **Par IDE**, choisissez d’abord la personne dans **IDE affichée** pour obtenir ses dates, ses postes et ses horaires. Le PDF couvre toujours le mois complet, même si une seule semaine est affichée à l’écran.

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
