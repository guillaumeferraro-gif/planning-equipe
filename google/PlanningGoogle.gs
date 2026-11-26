/** @OnlyCurrentDoc */
/* Google Apps Script V8, lié au classeur. L’application publique est épinglée
   à une révision publiée. Les états et le journal restent dans ce classeur. */
const PLANNING_COMMIT_ = 'baa2b33810a13540112aca93768b0c3d369fbd1b';
const PLANNING_HTML_SHA256_ = 'f5c044eeb6af36be75b7124ff27a1ef6d7e9faef49e3915f350c42d29dc96c70';
const PLANNING_SHEET_ = '_Planning_IDE_donnees_v1';
const PLANNING_MARK_ = 'PLANNING_IDE_STORAGE_V1';
const PLANNING_MAX_ = 16 * 1024 * 1024; // unités UTF-16 du document JSON
const PLANNING_CHUNK_ = 10000; // au plus 40 002 caractères par cellule après encodage

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Planning IDE')
    .addItem('Ouvrir le planning', 'ouvrirPlanning')
    .addItem('Actualiser la vue du classeur', 'actualiserVuePlanning')
    .addSeparator().addItem('Restaurer la sauvegarde précédente…', 'restaurerPlanningPrecedent')
    .addToUi();
}

function ouvrirPlanning() {
  if (!/^[a-f0-9]{40}$/.test(PLANNING_COMMIT_)) throw Error('Version de l’application non configurée.');
  const url='https://raw.githubusercontent.com/guillaumeferraro-gif/planning-equipe/'+PLANNING_COMMIT_+'/Planning-IDE.html';
  const reply=UrlFetchApp.fetch(url,{method:'get',followRedirects:false,muteHttpExceptions:true});
  if (reply.getResponseCode()!==200) throw Error('La version publiée du planning est momentanément inaccessible.');
  const html=reply.getContentText('UTF-8');
  if (!/^\s*<!doctype html>/i.test(html) || planningDigest_(html)!==PLANNING_HTML_SHA256_)
    throw Error('L’intégrité de la version publiée du planning n’a pas pu être vérifiée.');
  const dialog=HtmlService.createHtmlOutput(planningDialogHtml_(html)).setWidth(1320).setHeight(850);
  SpreadsheetApp.getUi().showModalDialog(dialog,'Planning IDE');
}

// Only the pinned, digest-verified public client is passed here. Keep its JS
// bytes out of HtmlService's inline-script rewriting and in the native frame.
function planningDialogHtml_(html) {
  const scripts=[];
  const shell=html.replace(/<script>([\s\S]*?)<\/script>/gi,function(block,source) {
    scripts.push(source);
    return '';
  });
  if (!scripts.length || /<script\b/i.test(shell) || !/<\/body>/i.test(shell))
    throw Error('La structure de l’application publiée est incompatible avec la fenêtre Google Sheets.');
  const encoded=Utilities.base64Encode(scripts.join('\n;\n'),Utilities.Charset.UTF_8);
  const payload=encoded.match(/.{1,8192}/g).join('\n');
  const boot=[
    '<p id="planning-boot-status" role="status" class="status" data-error="Le planning n’a pas pu démarrer. Fermez cette fenêtre puis rouvrez-la depuis le menu Planning IDE.">Ouverture du planning…</p>',
    '<div id="planning-bundle" hidden>',payload,'</div>',
    '<script>',
    '(function () {',
    '  var note = document.getElementById("planning-boot-status");',
    '  var failed = false;',
    '  function fail(error) {',
    '    failed = true;',
    '    note.setAttribute("role", "alert");',
    '    note.className = "status error";',
    '    note.textContent = note.getAttribute("data-error") + (error && error.message ? " " + error.message : "");',
    '  }',
    '  window.addEventListener("error", fail);',
    '  try {',
    '    var data = document.getElementById("planning-bundle");',
    '    var raw = atob(data.textContent);',
    '    data.remove();',
    '    var bytes = new Uint8Array(raw.length);',
    '    for (var i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);',
    '    var script = document.createElement("script");',
    '    if (document.currentScript && document.currentScript.nonce) script.nonce = document.currentScript.nonce;',
    '    script.textContent = new TextDecoder("utf-8", {fatal:true}).decode(bytes);',
    '    document.head.appendChild(script);',
    '    if (!failed && !document.getElementById("app").firstElementChild) fail();',
    '    if (!failed) note.remove();',
    '  } catch (error) { fail(error); }',
    '  finally { window.removeEventListener("error", fail); }',
    '})();',
    '</script>'
  ].join('\n');
  return shell.replace(/<\/body>/i,function() {return boot+'\n</body>';});
}

function planningLocked_(callback) {
  const lock=LockService.getDocumentLock();
  if (!lock) throw Error('Ce script doit être lié à un classeur Google Sheets.');
  lock.waitLock(30000);
  try { return callback(SpreadsheetApp.getActiveSpreadsheet()); }
  finally { lock.releaseLock(); }
}

function planningStore_(book,create) {
  let sheet=book.getSheetByName(PLANNING_SHEET_);
  if (!sheet && create) {
    sheet=book.insertSheet(PLANNING_SHEET_);
    sheet.getRange(1,1,1,3).setValues([[PLANNING_MARK_,'Copie A','Copie B']]);
    SpreadsheetApp.flush();
    if (book.getSheets().length>1) sheet.hideSheet();
  }
  if (sheet && sheet.getRange(1,1).getValue()!==PLANNING_MARK_)
    throw Error('L’onglet de stockage est illisible ou porte le nom d’un onglet déjà présent. Son contenu a été préservé.');
  return sheet;
}

// Journal contigu en colonne A. Une ligne validée constitue le seul point de
// commit. Les colonnes B et C reçoivent alternativement le nouvel état.
function planningRevision_(sheet) {
  if (!sheet) return 0;
  const row=sheet.getLastRow();
  if (row<=1) return 0;
  const bottom=sheet.getRange(row,1);
  const last=bottom.getValue()!=='' ? row : bottom.getNextDataCell(SpreadsheetApp.Direction.UP).getRow();
  return last-1;
}

function planningReceipt_(sheet,revision) {
  if (!revision) return null;
  const raw=sheet.getRange(revision+1,1).getValue();
  let r;
  try { r=JSON.parse(raw); } catch (_) {}
  if (!r || r.v!==1 || r.rev!==revision || ![2,3].includes(r.slot) ||
      !Number.isSafeInteger(r.parts) || r.parts<1 || r.parts>Math.ceil(PLANNING_MAX_/(PLANNING_CHUNK_-1)) ||
      !Number.isSafeInteger(r.size) || r.size<2 || r.size>PLANNING_MAX_ || !/^[a-f0-9]{64}$/.test(r.digest) ||
      typeof r.key!=='string' || !/^[A-Za-z0-9_-]{8,128}$/.test(r.key))
    throw Error('Journal de sauvegarde invalide à la révision '+revision+'.');
  return r;
}

function planningDigest_(body) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,body,Utilities.Charset.UTF_8)
    .map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join('');
}

function planningParts_(body) {
  const rows=[];
  for (let start=0;start<body.length;) {
    let end=Math.min(start+PLANNING_CHUNK_,body.length);
    const last=body.charCodeAt(end-1);
    if (end<body.length && last>=0xd800 && last<=0xdbff) end--;
    rows.push(['P:'+Utilities.base64Encode(body.slice(start,end),Utilities.Charset.UTF_8)]);
    start=end;
  }
  return rows;
}

function planningSnapshot_(sheet,receipt) {
  const rows=sheet.getRange(2,receipt.slot,receipt.parts,1).getValues();
  let body;
  try {
    body=rows.map(row=>{
      if (typeof row[0]!=='string' || !row[0].startsWith('P:') || row[0].length>40002) throw Error();
      return Utilities.newBlob(Utilities.base64Decode(row[0].slice(2))).getDataAsString('UTF-8');
    }).join('');
  } catch (_) {throw Error('Des fragments de la révision '+receipt.rev+' sont illisibles.');}
  if (body.length!==receipt.size || planningDigest_(body)!==receipt.digest)
    throw Error('La révision '+receipt.rev+' est incomplète. Utilisez le menu de restauration de la sauvegarde précédente.');
  return body;
}

function planningEnsureRows_(sheet,rows) {
  const existing=sheet.getMaxRows();
  if (existing<rows) sheet.insertRowsAfter(existing,rows-existing);
}

function readPlanning() {
  return planningLocked_(book=>{
    const sheet=planningStore_(book,false);
    const revision=planningRevision_(sheet);
    return {revision:revision,body:revision?planningSnapshot_(sheet,planningReceipt_(sheet,revision)):null};
  });
}

function planningProject_(book,body,revision) {
  try {
    refreshPlanningView_(book,body,revision);
    SpreadsheetApp.flush();
    return {ok:true,revision:revision};
  } catch (_) {
    return {ok:true,revision:revision,viewWarning:'La sauvegarde est enregistrée. Utilisez Planning IDE → Actualiser la vue du classeur pour mettre à jour l’onglet Planning.'};
  }
}

function writePlanning(expectedRevision,body,idempotencyKey) {
  if (!Number.isSafeInteger(expectedRevision) || expectedRevision<0 || expectedRevision>=Number.MAX_SAFE_INTEGER ||
      typeof idempotencyKey!=='string' || !/^[A-Za-z0-9_-]{8,128}$/.test(idempotencyKey))
    throw Error('Révision ou identifiant de sauvegarde invalide.');
  if (typeof body!=='string' || body.length<2 || body.length>PLANNING_MAX_)
    throw Error('Sauvegarde vide ou supérieure à 16 millions de caractères.');
  // UTF-8 cannot encode isolated UTF-16 surrogates. Standard JSON.stringify
  // escapes those automatically. Refuse an ambiguous manually supplied string.
  for (let i=0;i<body.length;i++) {
    const c=body.charCodeAt(i);
    if (c<0xd800 || c>0xdfff) continue;
    const next=body.charCodeAt(++i);
    if (c>0xdbff || !(next>=0xdc00 && next<=0xdfff)) throw Error('Le document JSON contient un caractère Unicode invalide.');
  }
  let state;
  try {state=JSON.parse(body);} catch (_) {throw Error('Le planning ne contient pas un document JSON valide.');}
  planningValidateState_(state);
  const digest=planningDigest_(body);
  return planningLocked_(book=>{
    let sheet=planningStore_(book,false);
    const revision=planningRevision_(sheet);
    const head=planningReceipt_(sheet,revision);
    if (expectedRevision<revision) {
      const receipt=planningReceipt_(sheet,expectedRevision+1);
      if (receipt.key===idempotencyKey) {
        if (receipt.digest!==digest || receipt.size!==body.length) throw Error('Cette tentative a déjà servi pour un autre contenu.');
        // Never project the old body over a newer snapshot when an ack was lost.
        if (receipt.rev===revision) return planningProject_(book,planningSnapshot_(sheet,head),revision);
        return {ok:true,revision:receipt.rev};
      }
    }
    if (revision!==expectedRevision) return {ok:false,conflict:true,revision:revision};
    if (!sheet) sheet=planningStore_(book,true);
    if (revision) {
      const keyInUse=sheet.getRange(2,1,revision,1).createTextFinder('"key":"'+idempotencyKey+'"')
        .useRegularExpression(false).matchCase(true).findNext();
      if (keyInUse) throw Error('Identifiant déjà utilisé pour une autre révision.');
      // Do not overwrite the recovery slot if the active snapshot was damaged.
      planningSnapshot_(sheet,head);
    }
    const rows=planningParts_(body);
    const receipt={v:1,rev:revision+1,slot:head && head.slot===2?3:2,parts:rows.length,size:body.length,
      digest:digest,key:idempotencyKey,at:new Date().toISOString()};
    planningEnsureRows_(sheet,Math.max(receipt.rev+1,rows.length+1));
    sheet.getRange(2,receipt.slot,rows.length,1).setValues(rows);
    SpreadsheetApp.flush();
    planningSnapshot_(sheet,receipt);
    sheet.getRange(receipt.rev+1,1).setValue(JSON.stringify(receipt));
    SpreadsheetApp.flush();
    return planningProject_(book,body,receipt.rev);
  });
}

function actualiserVuePlanning() {
  const result=planningLocked_(book=>{
    const sheet=planningStore_(book,false),revision=planningRevision_(sheet);
    if (!revision) return 'Aucun planning n’a encore été enregistré.';
    const body=planningSnapshot_(sheet,planningReceipt_(sheet,revision));
    const projected=planningProject_(book,body,revision);
    return projected.viewWarning || 'L’onglet Planning présente la révision '+revision+'.';
  });
  SpreadsheetApp.getUi().alert(result);
}

function restaurerPlanningPrecedent() {
  const ui=SpreadsheetApp.getUi();
  const seen=planningLocked_(book=>planningRevision_(planningStore_(book,false)));
  if (seen<2) {ui.alert('Aucune sauvegarde précédente disponible.');return;}
  if (ui.alert('Restaurer la sauvegarde précédente ?',
      'Le contenu de la révision '+(seen-1)+' redeviendra le planning partagé sous une nouvelle révision.',
      ui.ButtonSet.YES_NO)!==ui.Button.YES) return;
  const result=planningLocked_(book=>{
    const sheet=planningStore_(book,false),revision=planningRevision_(sheet);
    if (revision!==seen) throw Error('Le classeur a changé pendant la confirmation. Relancez la restauration.');
    const prev=planningReceipt_(sheet,revision-1);
    const body=planningSnapshot_(sheet,prev);
    const receipt=Object.assign({},prev,{rev:revision+1,key:Utilities.getUuid(),at:new Date().toISOString(),restored:revision-1});
    planningEnsureRows_(sheet,receipt.rev+1);
    sheet.getRange(receipt.rev+1,1).setValue(JSON.stringify(receipt));
    SpreadsheetApp.flush();
    return planningProject_(book,body,receipt.rev);
  });
  ui.alert(result.viewWarning || 'La sauvegarde précédente est restaurée. Révision '+result.revision+'.');
}

// Même validation du schéma, des identifiants, contrats, périodes et absences
// que dans le module domain.js de la version publiée. Les conflits de planning
// sont autorisés en brouillon. Les sauvegardes structurellement invalides sont refusées.
function planningValidateState_(input) {
  const SHIFT_MINUTES = Object.freeze({J:720,N:720,T:462,"-":0});
  const dayMilliseconds=86400000, maxTiihMinutes=2880;
  const paris=new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/Paris",hourCycle:"h23",
    year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});
  const dateCache=new Map();
  function requireValue(condition, message) {
    if (!condition) throw new Error(message);
  }
  function plain(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }
  function integer(value, min, max) {
    return Number.isSafeInteger(value) && value >= min && value <= max;
  }
  function validId(value) {
    return typeof value === "string" && value.length > 0 && value.length <= 200 &&
      !Object.prototype.hasOwnProperty.call(Object.prototype, value) && value !== "prototype";
  }
  function serial(day) {
    if (dateCache.has(day)) return dateCache.get(day);
    requireValue(typeof day === "string" && /^\d{4}-\d{2}-\d{2}$/.test(day), "Date invalide.");
    const epoch = Date.parse(day + "T00:00:00Z");
    requireValue(Number.isFinite(epoch) && new Date(epoch).toISOString().slice(0,10) === day,
      "Date de calendrier invalide.");
    const daysSinceEpoch = epoch / dayMilliseconds;
    if (dateCache.size > 12000) dateCache.clear();
    dateCache.set(day, daysSinceEpoch);
    return daysSinceEpoch;
  }
  function isoDay(number) {
    return new Date(number * dayMilliseconds).toISOString().slice(0,10);
  }
  function addDays(day, count) { return isoDay(serial(day) + count); }
  function weekday(day) { return ((serial(day) + 3) % 7 + 7) % 7; } // Monday = 0
  function dates(start, end) {
    const first = serial(start), last = serial(end);
    requireValue(last - first < 10000, "Période trop longue.");
    return Array.from({length: Math.max(0, last - first + 1)}, (_, i) => isoDay(first + i));
  }
  function phaseBounds(settings,mode) {
    if (mode==="N" || settings.rules_version!==2)
      return {min:settings.phase_min,target:settings.phase_target,max:settings.phase_max};
    return {min:settings.day_phase_min??14,target:settings.day_phase_target??15,max:settings.day_phase_max??16};
  }
  function checkQuotaPeriod(period) {
    requireValue(plain(period) && integer(period.percent,1,100),"La quotité temporaire doit être comprise entre 1 et 100 %.");
    serial(period.from);
    serial(period.to);
    requireValue(period.from<=period.to,"La fin de la période doit suivre son début.");
  }
  function localParts(epochMinute) {
    const parts = Object.fromEntries(paris.formatToParts(new Date(epochMinute*60000)).map(p => [p.type,p.value]));
    const day = [parts.year, parts.month, parts.day].join("-");
    return {day, minute: Number(parts.hour)*60+Number(parts.minute)};
  }
  function localEpoch(day, minute, advanceMissing=false) {
    const wall = serial(day)*1440 + minute;
    // Try offsets on both sides of a transition (and verify the local clock).
    // In the repeated autumn hour pick the earlier occurrence.
    const offsets = new Set();
    for (const t of [wall-1440,wall+1440]) {
      const actual = localParts(t);
      offsets.add(serial(actual.day)*1440+actual.minute-t);
    }
    const candidates = [...offsets].map(o => wall-o).sort((a,b) => a-b);
    let following;
    for (const epoch of candidates) {
      const actual = localParts(epoch);
      if (actual.day === day && actual.minute === minute) return epoch;
      if (actual.day===day && actual.minute>minute) following=epoch;
    }
    if (advanceMissing && following!==undefined) return following;
    throw new Error("Cet horaire local n’existe pas au changement d’heure.");
  }
  function moment(text) {
    const m = typeof text === "string" && /^(\d{4}-\d{2}-\d{2})(?:T(\d{2}):(\d{2})(?::00(?:\.0{1,6})?)?(Z|[+-]\d{2}:\d{2})?)?$/.exec(text);
    requireValue(m && Number(m[2]||0)<24 && Number(m[3]||0)<60,"Date et heure d’absence invalides.");
    serial(m[1]);
    const minute = Number(m[2]||0)*60 + Number(m[3]||0);
    const epoch = m[4] ? Date.parse(text)/60000 : localEpoch(m[1],minute);
    requireValue(Number.isInteger(epoch), "Horaire d’absence invalide.");
    return epoch;
  }
  function stamp(epoch) {
    const {day,minute} = localParts(epoch);
    const offset = serial(day)*1440+minute-epoch;
    const hhmm = m => String(Math.floor(m/60)).padStart(2,"0")+":"+String(m%60).padStart(2,"0");
    return day+"T"+hhmm(minute)+":00"+(offset<0?"-":"+")+hhmm(Math.abs(offset));
  }
  function checkedAbsence(state,input) {
    requireValue(plain(input) && validId(input.id) && state.nurses.some(n=>n.id===input.nurse_id),
      "IDE ou identifiant d’absence invalide.");
    requireValue(typeof input.kind === "string" && input.kind.trim().length>0,"Renseigner un motif d’absence.");
    const start=moment(input.start),end=moment(input.end);
    requireValue(start<end && end-start<=1101*1440,"La période d’absence doit durer entre une minute et trois ans.");
    const first=localParts(start).day,last=localParts(end-1).day;
    let credits = input.credits;
    if (credits === undefined) {
      const daily=input.daily_minutes ?? 462;
      requireValue(integer(daily,0,1440),"Le crédit quotidien doit être compris entre 0 et 24 heures.");
      credits=Object.fromEntries(dates(first,last).filter(d=>weekday(d)<5).map(d=>[d,daily]));
    }
    requireValue(plain(credits),"Crédits d’absence invalides.");
    for (const [d,v] of Object.entries(credits)) {
      serial(d);
      requireValue(d>=first && d<=last && integer(v,0,1440),"Crédit hors période ou durée invalide.");
    }
    return {id:input.id,nurse_id:input.nurse_id,kind:input.kind,start:stamp(start),end:stamp(end),credits:{...credits}};
  }
  function validateState(state) {
    requireValue(plain(state) && state.schema_version===2 && integer(state.revision,0,Number.MAX_SAFE_INTEGER),
      "Version de sauvegarde ou révision invalide.");
    for (const key of ["assignments","phases","reviewed","oat","tiih_changes","settings"]) {
      requireValue(plain(state[key]),"Rubrique de sauvegarde invalide : "+key);
    }
    for (const key of ["tiih_durations","tiih_history_durations"]) {
      if (!Object.hasOwn(state,key)) continue;
      requireValue(plain(state[key]),"Durées TIIH invalides dans la sauvegarde.");
      for (const [day,minutes] of Object.entries(state[key])) {
        serial(day);
        requireValue(integer(minutes,1,maxTiihMinutes),"Durée TIIH invalide le "+day+" (1 minute à 48 heures).");
      }
    }
    requireValue(Array.isArray(state.nurses) && Array.isArray(state.absences),
      "Équipe ou absences invalides.");
    const ids=new Set();
    for (const nurse of state.nurses) {
      requireValue(plain(nurse) && validId(nurse.id) && !ids.has(nurse.id) && typeof nurse.name==="string" &&
        nurse.name.trim() && Array.isArray(nurse.contracts) && nurse.contracts.length>0,"Identité ou contrat IDE invalide.");
      ids.add(nurse.id);
      if (nurse.active_from!=null) serial(nurse.active_from);
      if (nurse.active_until!=null) serial(nurse.active_until);
      requireValue(!nurse.active_from || !nurse.active_until || nurse.active_from<=nurse.active_until,
        "La sortie d’une IDE précède son entrée.");
      const periods=nurse.quota_periods??[];
      requireValue(Array.isArray(periods),"Périodes de quotité invalides.");
      const ordered=[...periods];
      const periodIds=new Set();
      for (const p of ordered) {
        checkQuotaPeriod(p);
        requireValue(validId(p.id) && !periodIds.has(p.id),"Identifiant de période de quotité invalide ou en double.");
        periodIds.add(p.id);
      }
      ordered.sort((a,b)=>a.from.localeCompare(b.from));
      for (let i=1;i<ordered.length;i++) requireValue(ordered[i].from>ordered[i-1].to,
        "Deux périodes de quotité se chevauchent pour la même IDE.");
      const seen=new Set();
      for (const c of nurse.contracts) {
        requireValue(plain(c) && !seen.has(c.from) && (c.percent===null||integer(c.percent,1,100)),
          "Date de contrat en double ou quotité invalide.");
        serial(c.from);
        seen.add(c.from);
      }
    }
    const s=state.settings;
    requireValue(s.rules_version===undefined || s.rules_version===1 || s.rules_version===2,
      "Cette sauvegarde utilise une version plus récente des règles.");
    requireValue(s.timezone==="Europe/Paris" && [null,"wall","elapsed"].includes(s.rest_clock) &&
      integer(s.phase_min,2,60) && integer(s.phase_target,s.phase_min,60) &&
      integer(s.phase_max,s.phase_target,60) && Array.isArray(s.extra_holidays),"Paramètres de planification invalides.");
    if (s.rules_version===2) requireValue(s.phase_min>=14 && s.phase_max<=21,
      "Les périodes de nuit doivent rester comprises entre 14 et 21 jours.");
    const dayPhase=phaseBounds(s,"J");
    requireValue(integer(dayPhase.min,2,60) && integer(dayPhase.target,dayPhase.min,60) &&
      integer(dayPhase.max,dayPhase.target,60),"Paramètres de période de jour invalides.");
    for (const d of s.extra_holidays) serial(d);
    for (const [year,m] of Object.entries(state.oat))
      requireValue(/^\d{4}$/.test(year) && integer(m,1,366*1440),"OAT annuel invalide.");
    for (const [d,row] of Object.entries(state.assignments)) {
      serial(d);
      requireValue(plain(row),"Affectations invalides.");
      for (const [nid,a] of Object.entries(row))
        requireValue(ids.has(nid) && plain(a) && Object.hasOwn(SHIFT_MINUTES,a.shift) &&
          typeof a.locked==="boolean" && typeof a.confirmed==="boolean","Affectation invalide.");
    }
    for (const [d,row] of Object.entries(state.phases)) {
      serial(d);
      requireValue(plain(row),"Périodes jour/nuit invalides.");
      for (const [nid,p] of Object.entries(row))
        requireValue(ids.has(nid) && plain(p) && ["J","N"].includes(p.mode) && integer(p.age,1,60),
          "Période jour/nuit invalide.");
    }
    for (const [d,reviewed] of Object.entries(state.reviewed)) {
      serial(d);
      requireValue(Array.isArray(reviewed) && reviewed.every(n=>ids.has(n)), "Historique invalide.");
    }
    const destinations=new Set();
    for (const [d,target] of Object.entries(state.tiih_changes)) {
      serial(d);
      if (target!==null) {
        serial(target);
        requireValue(!destinations.has(target),"Plusieurs postes TIIH sont déplacés vers le même jour.");
        destinations.add(target);
      }
    }
    const absIds=new Set(), intervals=new Map();
    for (const a of state.absences) {
      requireValue(plain(a) && plain(a.credits) && !absIds.has(a.id),"Identifiant ou crédits d’absence invalides.");
      checkedAbsence(state,a);
      absIds.add(a.id);
      if (!intervals.has(a.nurse_id)) intervals.set(a.nurse_id,[]);
      intervals.get(a.nurse_id).push([moment(a.start),moment(a.end)]);
    }
    for (const list of intervals.values()) {
      list.sort((a,b)=>a[0]-b[0]);
      for (let i=1;i<list.length;i++) requireValue(list[i][0]>=list[i-1][1],"Deux absences se chevauchent.");
    }
    return state;
  }
  return validateState(input);
}

// Vue du planning dans le classeur. Le journal canonique est géré séparément.
// Le serveur appelle cette fonction depuis le verrou du document.
function refreshPlanningView_(spreadsheet, body, revision) {
  const state = JSON.parse(body);
  const fallbackMonth = Utilities.formatDate(new Date(), "Europe/Paris", "yyyy-MM");
  const rows = planningReadableRows_(state, fallbackMonth);
  const sheet = planningReadableSheet_(spreadsheet);
  const headers = ["Date", "SMUR J · 08 h–20 h", "SMUR N · 20 h–08 h", "TIIH",
    "Début TIIH", "Fin TIIH", "Durée TIIH", "Situation du TIIH"];
  const priorRows = sheet.getLastRow();
  const requiredRows = rows.length + 1;
  const maxRows = sheet.getMaxRows(), maxCols = sheet.getMaxColumns();
  if (requiredRows > maxRows) sheet.insertRowsAfter(maxRows, requiredRows - maxRows);
  if (headers.length > maxCols) sheet.insertColumnsAfter(maxCols, headers.length - maxCols);

  const header = sheet.getRange(1, 1, 1, headers.length);
  header.setValues([headers]).setBackground("#173e52").setFontColor("#ffffff")
    .setFontWeight("bold").setVerticalAlignment("middle").setWrap(true);
  sheet.getRange("A1").setNote("Vue actualisée depuis Planning IDE · révision " + revision +
    ". Les changements de planning se font dans l’application. Le SMUR de nuit se termine le lendemain.");
  sheet.setFrozenRows(1);
  sheet.setRowHeight(1, 38);

  // Numeric date/time serials carry local wall time independently of the
  // spreadsheet timezone. RichTextValue writes literal names, never formulas.
  const literal = new Map();
  function textCell(name) {
    if (!literal.has(name)) literal.set(name, SpreadsheetApp.newRichTextValue().setText(name).build());
    return literal.get(name);
  }
  const values = rows.map(r => [r.date, "", "", "", r.begin, r.finish, r.duration, r.status]);
  sheet.getRange(2, 1, rows.length, headers.length).setValues(values);
  const namesRange = sheet.getRange(2, 2, rows.length, 3);
  namesRange.setNumberFormat("@");
  namesRange.setRichTextValues(rows.map(r => r.names.map(textCell)));
  sheet.getRange(2, 1, rows.length, 1).setNumberFormat("ddd dd/mm/yyyy");
  sheet.getRange(2, 5, rows.length, 1).setNumberFormat("hh:mm");
  sheet.getRange(2, 6, rows.length, 1).setNumberFormat("dd/mm/yyyy hh:mm");
  sheet.getRange(2, 7, rows.length, 1).setNumberFormat("[hh]:mm");
  sheet.getRange(2, 1, rows.length, 1).setBackgrounds(rows.map(r => [r.closedDay ? "#e7f0f3" : "#ffffff"]));
  if (priorRows > requiredRows)
    sheet.getRange(requiredRows + 1, 1, priorRows - requiredRows, headers.length).clearContent().clearFormat();
  sheet.setColumnWidth(1, 145);
  sheet.setColumnWidths(2, 3, 175);
  sheet.setColumnWidth(5, 100);
  sheet.setColumnWidth(6, 155);
  sheet.setColumnWidth(7, 100);
  sheet.setColumnWidth(8, 265);
  return sheet.getName();
}

function planningReadableSheet_(spreadsheet) {
  const key = "planning_ide_readable_view_v1";
  const props = PropertiesService.getDocumentProperties();
  const id = props.getProperty(key);
  const sheets = spreadsheet.getSheets();
  function owned(sheet) {
    return sheet.getDeveloperMetadata().some(meta => meta.getKey() === key &&
      meta.getValue() === String(sheet.getSheetId()));
  }
  const registered = sheets.find(sheet => String(sheet.getSheetId()) === id);
  if (registered && owned(registered)) return registered;
  const recovered = sheets.find(owned);
  if (recovered) {
    props.setProperty(key, String(recovered.getSheetId()));
    return recovered;
  }

  const taken = new Set(sheets.map(sheet => sheet.getName().toLowerCase()));
  let title = "Planning", suffix = 1;
  while (taken.has(title.toLowerCase())) {
    title = suffix === 1 ? "Planning IDE" : "Planning IDE (" + suffix + ")";
    suffix++;
  }
  const sheet = spreadsheet.insertSheet(title);
  const sheetId = String(sheet.getSheetId());
  sheet.addDeveloperMetadata(key, sheetId);
  props.setProperty(key, sheetId);
  return sheet;
}

// Gregorian Easter, metropolitan France public holidays and hospital closure dates.
function planningReadableHolidays_(year) {
  const floor = Math.floor;
  const a = year % 19, b = floor(year / 100), c = year % 100;
  const h = (19 * a + b - floor(b / 4) - floor((b - floor((b + 8) / 25) + 1) / 3) + 15) % 30;
  const l = (32 + 2 * (b % 4) + 2 * floor(c / 4) - h - (c % 4)) % 7;
  const n = h + l - 7 * floor((a + 11 * h + 22 * l) / 451) + 114;
  const easter = Date.UTC(year, floor(n / 31) - 1, n % 31 + 1);
  const fixed = ["01-01", "05-01", "05-08", "07-14", "08-15", "11-01", "11-11", "12-25"];
  return new Set(fixed.map(s => year + "-" + s).concat([1, 39, 50].map(offset =>
    new Date(easter + offset * 86400000).toISOString().slice(0, 10))));
}

function planningReadableRows_(state, fallbackMonth) {
  const assignments = state.assignments || {}, reviews = state.reviewed || {};
  const moves = state.tiih_changes || {}, durations = state.tiih_durations || {};
  const historic = state.tiih_history_durations || {};
  const movedTo = new Map();
  const months = new Set(), holidayYears = new Map();
  const extraHolidays = new Set((state.settings && state.settings.extra_holidays) || []);
  const people = new Map(state.nurses.map(n => [n.id, n.name]));
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const displayDate = day => day.slice(8) + "/" + day.slice(5, 7) + "/" + day.slice(0, 4);
  function includeDay(day) {
    if (typeof day === "string" && /^\d{4}-(0[1-9]|1[0-2])-\d{2}$/.test(day)) months.add(day.slice(0, 7));
  }
  [assignments, reviews, state.phases || {}, moves, durations, historic].forEach(table =>
    Object.keys(table).forEach(includeDay));
  for (const [from, to] of Object.entries(moves)) {
    if (to) { movedTo.set(to, from); includeDay(to); }
  }
  if (!months.size) months.add(fallbackMonth);
  const rows = [];
  for (const month of Array.from(months).sort()) {
    const year = Number(month.slice(0, 4)), m = Number(month.slice(5));
    if (!holidayYears.has(year)) holidayYears.set(year, planningReadableHolidays_(year));
    const holidays = holidayYears.get(year);
    const days = new Date(Date.UTC(year, m, 0)).getUTCDate();
    for (let i = 1; i <= days; i++) {
      const date = new Date(Date.UTC(year, m - 1, i)), day = date.toISOString().slice(0, 10);
      const weekday = date.getUTCDay(), holiday = holidays.has(day) || extraHolidays.has(day);
      const normal = [2, 4, 5].includes(weekday) && !holiday;
      const source = movedTo.get(day) || (!own(moves, day) && normal ? day : null);
      const duty = {J: [], N: [], T: []};
      const row = assignments[day] || {};
      for (const [id, item] of Object.entries(row))
        if (item && own(duty, item.shift)) duty[item.shift].push({name: people.get(id) || id, confirmed: item.confirmed});
      const known = Object.keys(row).length > 0 || (reviews[day] || []).length > 0;
      const missing = known ? "À pourvoir" : "Non renseigné";
      const hasTiih = duty.T.length > 0, relevant = Boolean(source) || hasTiih;
      const serial = date.getTime() / 86400000 + 25569;
      let minutes = 462;
      if (hasTiih && own(historic, day)) minutes = historic[day];
      else if (source && own(durations, source)) minutes = durations[source];
      else if (!source && hasTiih && !moves[day] && own(durations, day)) minutes = durations[day];

      const status = [];
      if (relevant) {
        if (source && source !== day) status.push("Déplacé du " + displayDate(source));
        if (!source && hasTiih) status.push("Affectation hors trame");
        if (duty.T.length > 1) status.push("Affectations multiples");
        else if (hasTiih) status.push(duty.T[0].confirmed ? "Confirmé" : "Planifié");
        else status.push(missing);
        if (hasTiih && !source && own(moves, day))
          status.push(moves[day] ? "déplacé au " + displayDate(moves[day]) : "occurrence supprimée");
      } else if (own(moves, day)) {
        status.push(moves[day] ? "Déplacé au " + displayDate(moves[day]) : "Supprimé");
      } else if (holiday) status.push("Férié");
      const start = serial + 9 / 24;
      const names = ["J", "N", "T"].map(code => duty[code].map(a => a.name).join(", ") ||
        (code === "T" && !relevant ? "—" : missing));
      rows.push({date: serial, names: names, begin: relevant ? start : "",
        finish: relevant ? start + minutes / 1440 : "", duration: relevant ? minutes / 1440 : "",
        status: status.join(" · "), closedDay: holiday || weekday === 0 || weekday === 6});
    }
  }
  return rows;
}
