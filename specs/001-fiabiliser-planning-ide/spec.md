# Feature Specification: Fiabiliser le planning de l'équipe IDE

**Feature Branch**: `codex/planning-ide-essai`

**Created**: 2026-11-24

**Status**: Cadrage précisé — paramètres individuels à compléter dans l’application

**Input**: Reprendre l'application existante pour sept IDE ; produire un planning modifiable
avec couverture SMUR jour et nuit, TIIH déplaçable ou supprimable, gestion des absences
créditées, OAT annuel paramétrable et périodes longues de jour ou de nuit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Générer et corriger un planning cohérent (Priority: P1)

Le responsable choisit une période, renseigne l'équipe et les contraintes connues,
génère une proposition, puis peut modifier les affectations. Il voit les conflits
avant de déclarer le planning valide et peut conserver un brouillon incomplet.

**Why this priority**: Assurer la couverture indispensable tout en permettant
l'ajustement quotidien du planning.

**Independent Test**: Utiliser sept agents fictifs et une période comportant un
changement de mois ; contrôler la proposition et une modification manuelle incompatible.

**Acceptance Scenarios**:

1. **Given** un jeu de disponibilités faisable, **When** une proposition est produite,
   **Then** chaque date possède exactement une affectation SMUR J et une SMUR N,
   et chaque TIIH maintenu est couvert.
2. **Given** une nuit du lundi 20 h au mardi 8 h, **When** le même agent reçoit
   un SMUR J mardi à 8 h ou un TIIH mardi à 9 h, **Then** la modification est
   signalée comme incompatible avec les 12 h de repos.
3. **Given** un dépassement de 48 h dans une fenêtre de sept jours ou quatre dates
   de prise de poste consécutives, **When** le contrôle est lancé, **Then** l'agent,
   les dates et la règle enfreinte sont affichés, y compris à cheval sur deux mois.
4. **Given** des affectations que le responsable a verrouillées, **When** il relance
   la génération, **Then** elles sont conservées ou leur incompatibilité est expliquée.
5. **Given** une recherche sans solution trouvée avant sa limite de temps,
   **When** le résultat est affiché, **Then** il n'est pas présenté comme une preuve
   que le planning est impossible.

### User Story 2 - Gérer les absences et les postes TIIH (Priority: P1)

Le responsable saisit une absence et sa valorisation, puis choisit les postes TIIH
à maintenir, supprimer ou déplacer afin d'ajuster le besoin de couverture.

**Why this priority**: Les absences multiples ne doivent conduire ni à affecter un agent
absent ni à supprimer implicitement une couverture obligatoire.

**Independent Test**: Ajouter des absences sur des agents fictifs, supprimer un TIIH
sur une date et en déplacer un autre ; comparer besoins, affectations et compteurs.

**Acceptance Scenarios**:

1. **Given** une absence couvrant tout ou partie d'un poste, **When** une affectation
   est créée ou contrôlée, **Then** le chevauchement est interdit et visible.
2. **Given** un TIIH supprimé pour une date, **When** le planning est recalculé,
   **Then** le besoin TIIH disparaît pour cette seule date et les deux postes SMUR restent.
3. **Given** un déplacement TIIH vers une date autorisée sans TIIH existant,
   **When** le déplacement est enregistré, **Then** le poste d'origine est désactivé
   et un seul poste apparaît à destination, avec un lien vers l'origine.
4. **Given** une destination fériée ou déjà occupée par un TIIH, **When** le responsable
   tente le déplacement, **Then** l'opération est refusée avec une explication.
5. **Given** une absence avec un crédit d'heures explicite, **When** les compteurs sont
   recalculés, **Then** ce crédit apparaît une seule fois dans la rubrique absences,
   séparément du travail effectué.
6. **Given** un agent absent malgré une ancienne affectation enregistrée,
   **When** l'absence est saisie, **Then** le conflit est visible et l'ancienne affectation
   n'est pas comptée silencieusement comme du travail effectivement réalisé.

### User Story 3 - Suivre l'année sans connaître encore l'OAT (Priority: P1)

Le responsable consulte les heures planifiées, réalisées si elles ont été confirmées,
et créditées pour chaque IDE sur l'année civile, puis renseigne l'OAT lorsqu'il le connaît.

**Why this priority**: Les compteurs restent utilisables sans inventer la valeur annuelle
de référence ni mélanger plusieurs années.

**Independent Test**: Saisir des postes et absences sur deux années, laisser l'OAT vide,
puis le renseigner ; vérifier les trois composantes du compteur et le solde.

**Acceptance Scenarios**:

1. **Given** un OAT non renseigné, **When** le tableau annuel est consulté,
   **Then** les heures connues sont affichées et le solde est indiqué « OAT à renseigner ».
2. **Given** une valeur annuelle connue et une quotité connue, **When** le tableau est
   recalculé, **Then** la cible individuelle et son calcul sont visibles.
3. **Given** des heures enregistrées sur plusieurs années,
   **When** une année est sélectionnée, **Then** les autres années ne contribuent pas au total.
4. **Given** un poste TIIH complet, **When** il est comptabilisé,
   **Then** il vaut exactement 7 h 42 ; un SMUR J ou N complet vaut 12 h.
5. **Given** un planning futur, **When** les compteurs sont consultés,
   **Then** les heures prévisionnelles sont distinguées des heures confirmées.
6. **Given** un crédit d'absence encore indéterminé, **When** les compteurs sont consultés,
   **Then** le total concerné est signalé incomplet et aucun solde définitif n'est affiché.

### User Story 4 - Organiser les périodes jour et nuit (Priority: P1)

Chaque IDE alterne des périodes d'environ une quinzaine dédiées à la nuit et au jour,
avec ses repos à l'intérieur. Le responsable visualise ces périodes sur plusieurs mois.

**Why this priority**: Éviter les changements fréquents de régime jour/nuit.

**Independent Test**: Construire un horizon de deux mois avec périodes, repos et
week-ends ; vérifier les transitions retenues selon les réglages enregistrés.

**Acceptance Scenarios**:

1. **Given** une période dédiée à la nuit, **When** les affectations sont générées,
   **Then** seuls SMUR N et repos/absences sont placés dans cette période.
2. **Given** une période dédiée au jour, **When** les affectations sont générées,
   **Then** SMUR J et TIIH sont possibles, ainsi que repos/absences, mais pas SMUR N.
3. **Given** une frontière de mois au milieu d'une période,
   **When** le mois suivant est ouvert, **Then** le régime se poursuit sans remise à zéro.
4. **Given** un week-end travaillé, **When** sa cohérence est contrôlée,
   **Then** les deux prises de poste du samedi et du dimanche sont groupées
   et aucune prise de poste supplémentaire n'est placée le lundi.
5. **Given** une frontière de régime empêchant de couvrir un week-end complet,
   **When** la génération est demandée, **Then** le conflit est signalé ;
   le régime ne change pas implicitement pour résoudre la difficulté.

### Edge Cases

- Nuit traversant minuit, une limite de mois, le 31 décembre ou un changement d'heure.
- Dimanche nuit se terminant le lundi à 8 h : le repos du lundi signifie, selon
  l'hypothèse actuelle, aucune nouvelle prise de poste le lundi.
- Repos de 12 h exactement autorisé ; repos inférieur à 12 h refusé.
- TIIH après une nuit ; nuit du même jour après un TIIH ; double affectation ou chevauchement.
- Absence à cheval sur une nuit, plusieurs mois ou deux années ; deux absences qui se chevauchent.
- Absence décidée avant que le planning soit construit, ou après publication du planning.
- Plusieurs absences rendant la couverture SMUR impossible même sans aucun TIIH.
- Annulation, restauration ou déplacement d'un TIIH déjà affecté, sans maintien fantôme
  de l'ancienne affectation.
- Déplacement TIIH sur un lundi ou un week-end : mêmes repos et règles de week-end
  que pour tout autre travail ; refuser ou signaler toute incompatibilité.
- Frontière de quinzaine au milieu d'un week-end ; mois de 28, 29, 30 ou 31 jours.
- Historique du mois précédent manquant : état « contrôle des limites incomplet »,
  jamais validation globale supposée.
- OAT absent, quotité absente, crédit d'absence indéterminé ou changement de quotité.
- Planning en 2027 et au-delà ; reprise des anciens plannings sans perdre les affectations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT gérer une équipe initiale de sept IDE, avec identité,
  quotité et éventuelles restrictions explicitement renseignées et modifiables.
- **FR-002**: Le besoin SMUR J DOIT être exactement un IDE de 8 h à 20 h chaque jour,
  week-ends et jours fériés compris.
- **FR-003**: Le besoin SMUR N DOIT être exactement un IDE de 20 h à 8 h le lendemain,
  chaque jour, et le poste DOIT être affiché à sa date de début.
- **FR-004**: Le besoin TIIH par défaut DOIT être un IDE de 9 h à 16 h 42 les mardis,
  jeudis et vendredis non fériés.
- **FR-005**: Le responsable DOIT pouvoir supprimer/restaurer un TIIH à une date précise,
  ou déplacer ce poste vers une autre date non fériée sans créer un doublon.
  La génération ne DOIT pas supprimer ou déplacer un TIIH de sa propre initiative.
- **FR-006**: Un IDE ne DOIT pas recevoir des postes qui se chevauchent, ni deux postes
  ayant moins de 12 h de repos entre fin effective et début effectif.
- **FR-007**: Le travail effectif DOIT respecter 48 h maximum sur toute fenêtre
  de sept jours ; la convention temporelle de vérification retenue doit être visible.
- **FR-008**: Le système DOIT interdire plus de trois dates consécutives de prise de poste,
  y compris lorsque TIIH est impliqué ou qu'un mois se termine.
- **FR-009**: Le travail du samedi et du dimanche DOIT être groupé pour un agent,
  sans nouvelle prise de poste le lundi suivant. Tout TIIH déplacé reste soumis
  à cette règle.
- **FR-010**: Les régimes jour et nuit DOIVENT former des périodes longues et rester
  continus entre les mois. Les périodes durent environ quinze jours ; les nuits isolées restent autorisées mais doivent être minimisées. Réglage initial proposé : minimum 14, cible 15, maximum 16 jours, modifiable dans l’application.
- **FR-011**: Le responsable DOIT pouvoir enregistrer, modifier et annuler des absences
  datées : maladie, congés annuels, RTT, grossesse/maternité, formation,
  congés exceptionnels et temps partiel thérapeutique. Cette dernière catégorie
  doit pouvoir représenter une indisponibilité partielle et sa quotité applicable.
  Aucun aménagement spécifique des postes pour grossesse n'est inclus.
- **FR-012**: Toute absence DOIT contribuer au compteur avec un crédit explicite,
  sans devenir du travail effectif pour le contrôle de repos ou de charge travaillée.
  Le crédit par défaut vaut 7 h 42 par date du lundi au vendredi. Une absence du vendredi au lundi rend indisponible pendant quatre jours et crédite deux journées. Des créneaux et crédits de durée différente doivent pouvoir être saisis explicitement.
- **FR-013**: Le système DOIT distinguer absence, repos, poste requis non couvert,
  poste supprimé et affectation existante.
- **FR-014**: L'OAT DOIT rester configurable par année civile, commun par défaut aux
  personnels de jour, de nuit et alternants ; son absence ne DOIT pas bloquer
  les vues de planning ni les compteurs d'heures connus.
- **FR-015**: La cible individuelle DOIT être calculée à partir de l'OAT et de la
  quotité connue, avec des dates d'effet en cas de changement.
  Les quotités sont configurables individuellement. Deux IDE sont à 80 % et une à 100 % ; les quatre autres quotités restent non renseignées. Toutes peuvent travailler sur les trois postes. Aucun 100 % ne doit être déduit d’une valeur manquante.
- **FR-016**: Le tableau annuel DOIT afficher séparément travail planifié, travail confirmé,
  absences créditées, total comptabilisé, cible et écart lorsqu'ils sont calculables.
- **FR-017**: Les heures DOIVENT être conservées avec précision à la minute. Les postes
  complets valent 720 minutes pour SMUR J/N et 462 minutes pour TIIH, pauses comprises.
- **FR-018**: Les contrôles DOIVENT intégrer les affectations connues autour de la période
  modifiée ; une information de frontière manquante DOIT être signalée.
- **FR-019**: Le responsable DOIT pouvoir générer, modifier, sauvegarder, recharger
  et verrouiller des affectations ; un brouillon incompatible doit rester distinct
  d'un planning valide. Une régénération doit préserver le planning sauvegardé
  jusqu'à acceptation explicite de la nouvelle proposition.
- **FR-020**: Le système DOIT distinguer résultat valide, conflit identifié, absence
  de solution démontrée et recherche interrompue sans conclusion.
- **FR-021**: Les règles confirmées de couverture, repos, charge et absence DOIVENT
  être prioritaires sur l'équilibrage de la charge entre IDE.
- **FR-022**: Les nouvelles données de personnel et absences DOIVENT être conservées
  hors du dépôt de code et les exemples partagés DOIVENT utiliser des agents fictifs.
- **FR-023**: La reprise DOIT préserver les anciens plannings et signaler leur contrôle
  au regard des nouvelles règles ; un ancien enregistrement n'est pas une preuve de validité.
- **FR-024**: Les compteurs DOIVENT filtrer l'année civile sélectionnée et signaler
  les mois ou crédits incomplets ; la navigation ne doit pas être limitée à 2026.
- **FR-025**: L'équilibrage DOIT tenir compte des quotités connues et montrer la charge
  de chaque IDE ; il ne doit pas viser des totaux identiques pour des quotités différentes.
  Sans OAT, il peut équilibrer le travail mais ne doit pas prétendre atteindre une cible annuelle.

### Key Entities *(include if feature involves data)*

- **IDE** : identifiant, nom d'affichage, quotité avec dates d'effet, restrictions.
- **Poste** : type, date de début, heures de début/fin, durée créditée, caractère obligatoire.
- **Besoin TIIH** : date, état maintenu/supprimé/déplacé et lien origine-destination.
- **Affectation** : IDE, poste, état prévu/confirmé et verrouillage.
- **Période de régime** : IDE, début, fin, régime jour ou nuit, continuité entre mois.
- **Absence** : IDE, type, intervalle, crédit, mode de valorisation, état du crédit.
- **Paramètres annuels** : année civile, OAT facultatif, calendrier férié.
- **Planning** : période, affectations, brouillon/validé, résultats des contrôles.
- **Compteur annuel** : travail prévu, travail confirmé, absences, total, cible, écart,
  état de complétude.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tous les plannings déclarés valides couvrent 100 % des besoins SMUR
  et des TIIH maintenus et respectent 100 % des contraintes confirmées.
- **SC-002**: Tous les cas de vérification avec moins de 12 h de repos, une absence
  chevauchante, quatre jours consécutifs ou une charge excessive sont détectés,
  y compris aux frontières de mois et d'année.
- **SC-003**: Le responsable peut supprimer ou déplacer un TIIH et en voir les
  conséquences sur le planning en moins d'une minute.
- **SC-004**: Les compteurs sont exacts à la minute pour les scénarios de référence ;
  aucun crédit n'est ajouté deux fois et aucune heure d'une autre année n'est incluse.
- **SC-005**: Les décisions de régime de durée des périodes enregistrées sont respectées dans tous les
  scénarios de vérification portant sur deux mois successifs.
- **SC-006**: Pour un jeu faisable de sept IDE sur un mois, le responsable obtient
  une proposition ou un état explicite de recherche en moins de 30 secondes.
- **SC-007**: Sauvegarder puis rouvrir un planning conserve 100 % de ses affectations,
  absences, crédits explicites, changements TIIH et verrouillages.
- **SC-008**: Sans OAT ou avec un crédit incomplet, aucune cible ni aucun solde
  trompeur n'est présenté ; les informations déjà connues restent consultables.

## Assumptions

- Première version : un responsable utilisant l'application existante, en français,
  avec une vue mensuelle et un suivi annuel. Comptes multiples, publication en ligne
  et intégration RH ne sont pas encore demandés et ne sont pas définis ici.
- Le calendrier français déjà utilisé constitue le point de départ ; des exceptions
  locales doivent pouvoir être renseignées. Ce choix ne présume pas le lieu de l'hôpital.
- Les 48 h concernent le travail effectué ; les crédits d'absence sont séparés.
  Hypothèse de vérification à exposer : heures réellement chevauchantes dans toute
  fenêtre glissante de 168 h ; les durées créditées restent celles confirmées par le responsable.
- Les trois jours consécutifs se rapportent aux dates de début des postes. La nuit
  du dimanche finit le lundi matin, sans nouvelle prise de poste le lundi.
- Le week-end SMUR conserve le même type de poste le samedi et le dimanche, comme
  dans l'application existante. Un TIIH déplacé doit rester compatible avec cette
  organisation, la couverture et les 12 h de repos.
- Un déplacement TIIH conserve son horaire et sa durée, désactive son besoin d'origine,
  et ne crée pas plus d'un TIIH par date.
- La nuit est rattachée à sa date de début pour l'affichage et, provisoirement, pour
  les compteurs mensuels/annuels ; le repos utilise toujours ses bornes réelles.
  Le rattachement comptable au 31 décembre pourra être adapté à la convention de l'hôpital.
- Aucune valeur chiffrée d’OAT n’est présumée. Le crédit d’absence par défaut est celui confirmé : 462 minutes par jour du lundi au vendredi.
- Les quotités individuelles manquantes sont des données à compléter dans l’application, pas des règles à inventer.

## Clarifications — 2026-11-24

- Périodes d’environ quinze jours ; nuits isolées possibles, à limiter.
- Crédit de 7 h 42 du lundi au vendredi ; créneaux et durées personnalisables.
- Toutes les IDE sont polyvalentes J/N/TIIH. Deux quotités de 80 % et une de 100 % sont connues, sans association nominative ; quatre valeurs restent à saisir.
- Publication du cahier des charges dans le dépôt public explicitement autorisée.
- Convention de repos confirmée : horaires affichés ; 20 h–8 h compte pour 12 h même au changement d’heure. La convention reste visible dans les paramètres.

## Publication — 2026-11-25

- Publication de la version d’essai complète sur GitHub explicitement demandée par le responsable.
- Le dépôt contient le code, les tests et les instructions de lancement ; les données de l’équipe restent locales.
