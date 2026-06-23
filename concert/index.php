<?php
require_once __DIR__ . '/../db.php';

$id = basename(explode('?', $_SERVER['REQUEST_URI'])[0]);

$db = get_db();
$stmt = $db->prepare("SELECT * FROM concerts WHERE id = :id");
$stmt->execute([':id' => $id]);
$concert = $stmt->fetch();

if (!$concert) {
    http_response_code(404);
    echo '<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem"><h1>Concert introuvable</h1><p><a href="../">← Retour</a></p></body></html>';
    exit;
}

// state est stocké en JSON dans SQLite, on le décode pour le passer au JS
$concert['state'] = json_decode($concert['state'] ?? '{}', true) ?: [];

$stateJson   = json_encode($concert['state'] ?? [], JSON_UNESCAPED_UNICODE);
$concertJson = json_encode([
    'id' => $concert['id'], 'name' => $concert['name'] ?? '',
    'date' => $concert['date'] ?? '', 'respo' => $concert['respo'] ?? '',
    'mandataire' => $concert['mandataire'] ?? '',
], JSON_UNESCAPED_UNICODE);
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CONAN — <?= htmlspecialchars($concert['name'] ?: 'Concert') ?></title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Josefin+Sans:wght@400;600;700&display=swap');
:root {
  --green:#3a7d44;--green-dark:#2a5e32;--green-light:#d6edd9;--green-pale:#f4faf4;
  --green-mid:#eaf4eb;--white:#fff;--ink:#1a2e1d;--muted:#6b8c6e;--border:#c2ddc5;
  --cond-bg:#f0f8f1;--yesno-bg:#eef6ef;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;background:var(--green-pale);color:var(--ink);min-height:100vh;padding:0 0 5rem;}
.site-header{background:var(--green);padding:1.25rem 1.25rem 1rem;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(30,69,38,.18);}
.header-inner{max-width:680px;margin:0 auto;}
.header-top{display:flex;align-items:center;gap:.75rem;}
.back-link{color:rgba(255,255,255,.7);text-decoration:none;font-size:.8rem;font-family:'Josefin Sans',sans-serif;letter-spacing:.04em;transition:color .15s;flex-shrink:0;}
.back-link:hover{color:white;}
.header-title{font-family:'Josefin Sans',sans-serif;font-weight:700;font-size:1.05rem;color:white;letter-spacing:.04em;text-transform:uppercase;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.save-indicator{font-size:.7rem;color:rgba(255,255,255,.6);font-family:'Josefin Sans',sans-serif;letter-spacing:.04em;flex-shrink:0;transition:color .3s;}
.save-indicator.saving{color:var(--green-light);}
.save-indicator.saved{color:rgba(255,255,255,.9);}
.header-prog{display:flex;align-items:center;gap:.75rem;margin-top:.75rem;}
.prog-track{flex:1;height:4px;background:rgba(255,255,255,.2);border-radius:2px;overflow:hidden;}
.prog-fill{height:100%;background:var(--green-light);border-radius:2px;transition:width .35s ease;}
.prog-text{font-family:'Josefin Sans',sans-serif;font-size:.75rem;color:rgba(255,255,255,.75);letter-spacing:.05em;white-space:nowrap;}
.meta-section{max-width:680px;margin:1.5rem auto 0;padding:0 1rem;}
.meta-card{background:var(--white);border:1.5px solid var(--border);border-radius:8px;padding:1rem 1.125rem;display:grid;grid-template-columns:1fr 1fr;gap:.875rem 1.25rem;}
.meta-field{display:flex;flex-direction:column;gap:.25rem;}
.meta-field.full{grid-column:1/-1;}
.meta-label{font-family:'Josefin Sans',sans-serif;font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600;}
.meta-input{font-family:'Nunito',sans-serif;font-size:.875rem;background:transparent;border:none;border-bottom:1.5px solid var(--border);padding:.25rem 0;color:var(--ink);outline:none;transition:border-color .2s;width:100%;}
.meta-input:focus{border-color:var(--green);}
.meta-input::placeholder{color:var(--border);}
.meta-textarea{font-family:'Nunito',sans-serif;font-size:.82rem;background:var(--green-pale);border:1.5px solid var(--border);border-radius:6px;padding:.5rem .65rem;color:var(--ink);outline:none;resize:vertical;min-height:68px;width:100%;transition:border-color .2s;line-height:1.5;}
.meta-textarea:focus{border-color:var(--green);}
.meta-textarea::placeholder{color:var(--border);}
.steps{max-width:680px;margin:1.25rem auto 0;padding:0 1rem;display:flex;flex-direction:column;gap:.875rem;}
.step{background:var(--white);border:1.5px solid var(--border);border-radius:8px;overflow:hidden;transition:border-color .2s,box-shadow .2s;}
.step.completed{border-color:var(--green);box-shadow:0 0 0 1px var(--green-light);}
.step.parallel{border-left:4px solid var(--green-light);}
.step-header{display:flex;align-items:center;gap:.75rem;padding:.875rem 1rem;cursor:pointer;user-select:none;background:var(--green-mid);transition:background .15s;}
.step.parallel .step-header{background:#eaf5eb;}
.step.completed .step-header{background:var(--green-light);}
.step-num{font-family:'Josefin Sans',sans-serif;font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--green);background:rgba(58,125,68,.1);padding:.15rem .45rem;border-radius:3px;white-space:nowrap;}
.step.completed .step-num{background:var(--green);color:white;}
.step-title{font-family:'Josefin Sans',sans-serif;font-weight:700;font-size:.95rem;letter-spacing:.02em;flex:1;color:var(--ink);}
.step-badge{font-family:'Josefin Sans',sans-serif;font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;color:var(--green);border:1px solid var(--green-light);background:var(--white);padding:.1rem .4rem;border-radius:3px;white-space:nowrap;}
.step-chevron{color:var(--muted);font-size:.65rem;transition:transform .2s;flex-shrink:0;}
.step.open .step-chevron{transform:rotate(180deg);}
.step-body{display:none;}
.step.open .step-body{display:block;}
.item{border-bottom:1px solid var(--green-pale);padding:.75rem 1rem;transition:background .12s;}
.item:last-child{border-bottom:none;}
.item:hover{background:var(--green-pale);}
.item-row{display:flex;align-items:flex-start;gap:.75rem;}
.check-wrap{flex-shrink:0;margin-top:2px;cursor:pointer;}
.check-box{width:18px;height:18px;border:2px solid var(--border);border-radius:4px;display:flex;align-items:center;justify-content:center;transition:all .15s;background:white;}
.check-wrap:hover .check-box{border-color:var(--green);}
.check-box.checked{background:var(--green);border-color:var(--green);}
.check-box.checked::after{content:'';display:block;width:9px;height:5px;border-left:2px solid white;border-bottom:2px solid white;transform:rotate(-45deg) translateY(-1px);}
.item-content{flex:1;}
.item-label{font-size:.9rem;font-weight:600;line-height:1.4;cursor:pointer;}
.item-label.done{text-decoration:line-through;color:var(--muted);font-weight:400;}
.item-hint{margin-top:.3rem;font-size:.775rem;color:var(--muted);font-style:italic;line-height:1.5;font-weight:400;}
.item-hint a{color:var(--green);text-underline-offset:2px;}
.text-field-wrap{margin-top:.5rem;}
.text-field-area{font-family:'Nunito',sans-serif;font-size:.82rem;width:100%;min-height:64px;border:1.5px solid var(--border);border-radius:6px;padding:.5rem .65rem;color:var(--ink);background:var(--green-pale);resize:vertical;outline:none;line-height:1.5;transition:border-color .2s;}
.text-field-area:focus{border-color:var(--green);}
.text-field-area::placeholder{color:var(--border);font-style:italic;}
.text-field-done-row{display:flex;align-items:center;gap:.5rem;margin-top:.5rem;}
.text-field-done-label{font-size:.75rem;color:var(--muted);cursor:pointer;font-weight:600;font-family:'Josefin Sans',sans-serif;letter-spacing:.05em;text-transform:uppercase;}
.text-field-done-label.done{color:var(--green);}
.yesno-item{border-bottom:1px solid var(--green-pale);padding:.7rem 1rem;background:var(--yesno-bg);}
.yesno-item:last-child{border-bottom:none;}
.yesno-row{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;}
.yesno-label{font-size:.9rem;font-weight:700;flex:1;color:var(--green-dark);font-family:'Josefin Sans',sans-serif;letter-spacing:.02em;}
.yesno-hint{font-size:.75rem;color:var(--muted);font-style:italic;margin-top:.2rem;font-weight:400;}
.yesno-question{font-size:.62rem;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;font-family:'Josefin Sans',sans-serif;}
.yesno-btns{display:flex;gap:.35rem;flex-wrap:wrap;}
.yn-btn{font-family:'Josefin Sans',sans-serif;font-size:.68rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;padding:.25rem .65rem;border:1.5px solid var(--border);border-radius:4px;cursor:pointer;background:white;color:var(--muted);transition:all .15s;white-space:nowrap;}
.yn-btn:hover{border-color:var(--green);color:var(--green);}
.yn-btn.active-neutral{background:var(--ink);border-color:var(--ink);color:white;}
.yn-btn.active-yes{background:var(--green);border-color:var(--green);color:white;}
.sub-items{display:none;border-left:3px solid var(--green-light);margin:0 1rem;background:var(--cond-bg);border-radius:0 0 6px 6px;}
.sub-items.visible{display:block;animation:fadeIn .18s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px);}to{opacity:1;transform:translateY(0);}}
.sub-item{display:flex;align-items:center;gap:.6rem;padding:.55rem 1rem;border-bottom:1px solid var(--green-pale);}
.sub-item:last-child{border-bottom:none;}
.sub-check{width:15px;height:15px;border:2px solid var(--border);border-radius:3px;flex-shrink:0;display:flex;align-items:center;justify-content:center;cursor:pointer;background:white;transition:all .15s;}
.sub-check:hover{border-color:var(--green);}
.sub-check.checked{background:var(--green);border-color:var(--green);}
.sub-check.checked::after{content:'';display:block;width:7px;height:4px;border-left:1.5px solid white;border-bottom:1.5px solid white;transform:rotate(-45deg) translateY(-1px);}
.sub-label{font-size:.83rem;cursor:pointer;flex:1;font-weight:600;}
.sub-label.done{text-decoration:line-through;color:var(--muted);font-weight:400;}
</style>
</head>
<body>
<div class="site-header">
  <div class="header-inner">
    <div class="header-top">
      <a class="back-link" href="../">← Tous les concerts</a>
      <span class="header-title" id="header-title"><?= htmlspecialchars($concert['name'] ?: 'Concert sans nom') ?></span>
      <span class="save-indicator" id="save-indicator">—</span>
    </div>
    <div class="header-prog">
      <div class="prog-track"><div class="prog-fill" id="prog-fill" style="width:0%"></div></div>
      <span class="prog-text" id="prog-text">0 / 0</span>
    </div>
  </div>
</div>

<div class="meta-section">
  <div class="meta-card">
    <div class="meta-field"><span class="meta-label">Nom du concert</span><input class="meta-input" id="meta-nom" type="text" placeholder="—" /></div>
    <div class="meta-field"><span class="meta-label">Date</span><input class="meta-input" id="meta-date" type="text" placeholder="—" /></div>
    <div class="meta-field"><span class="meta-label">Respo Negi</span><input class="meta-input" id="meta-respo" type="text" placeholder="—" /></div>
    <div class="meta-field full"><span class="meta-label">Contact mandataire</span><textarea class="meta-textarea" id="meta-mandataire" placeholder="Nom, téléphone, email…"></textarea></div>
  </div>
</div>

<div class="steps" id="steps"></div>

<script>
const CONCERT = <?= $concertJson ?>;
let S = <?= $stateJson ?>;

const STEPS = [
  { id:"s1", num:"Étape 1", title:"Sondage préalable", items:[
    { id:"s1_1", label:"Création du sondage", hint:'Copier le sondage template et suivre le mode d\'emploi : <a href="https://moodle.negitachi.fr/course/section.php?id=501" target="_blank">https://moodle.negitachi.fr/course/section.php?id=501</a>' },
    { id:"s1_2", label:"Mail d'info membres", hint:"Envoyer un mail de contexte avec le lien du sondage." },
    { id:"s1_3", label:"#info-importantes", hint:"Poster le lien dans #infos-importantes, ou déléguer à quelqu'un qui a les droits." },
    { id:"s1_4", label:"Relances", hint:"Vérifier le nombre de réponses manquantes et relancer si besoin." },
    { id:"s1_5", label:"Décision", hint:"Télécharger le .xlsx, le cleaner, partager dans #waconan pour acter la participation." },
  ]},
  { id:"s2", num:"Étape 2", title:"Moodle", parallel:true, items:[
    { id:"s2_1", label:"Création du cours Moodle", hint:"Demander à Eve ou au bureau." },
    { id:"s2_2", label:"Informations basiques", hint:"Zone texte et média : lieu, heure (mettre ? si inconnu)." },
    { id:"s2_3", label:"Poireaux présents", hint:"Créer la section et la remplir avec les infos du sondage préalable." },
    { id:"s2_4", label:"Mail de récap", hint:"Objet : [Concert] Nom - Date. Valider participation, copier le lien Moodle, demander de prévenir si changement." },
  ]},
  { id:"s2b", num:"Étape 2'", title:"Orga interne", parallel:true, items:[
    { id:"s2b_1", label:"ComCom au courant" },
    { id:"s2b_2", label:"Éléments à transmettre à ComCom (#ComcomConan)", type:"textfield", placeholder:"Pack presse, description, logos…" },
    { id:"s2b_4", label:"CoTech au courant", type:"cotech" },
    { id:"s2b_3", label:"Trouver une salle ?", type:"yesno", subs:[
      { id:"s2b_3a", label:"Se répartir les démarches avec le Bureau" },
      { id:"s2b_3b", label:"Confirmer la réservation de salle" },
      { id:"s2b_3c", label:"Vérifier les accès et la logistique sur place" },
    ]},
    { id:"s2b_5", label:"Organisation des transports ?", type:"yesno", subs:[
      { id:"s2b_5a", label:"Sondage transport dans Moodle" },
      { id:"s2b_5b", label:"Dépouillage du sondage" },
      { id:"s2b_5c", label:"Création d'un Google Doc de coordination" },
    ]},
  ]},
  { id:"s3", num:"Étape 3", title:"Suivi de la préparation", items:[
    { id:"s3_1", label:"PL reçue des Wacos" },
    { id:"s3_2", label:"PL dans Moodle" },
    { id:"s3_3", label:"PL envoyée par mail" },
    { id:"s3_5", label:"SACEM ?", type:"yesno", subs:[
      { id:"s3_5a", label:"Contacter Lia (ou sa succession)" },
      { id:"s3_5b", label:"Effectuer la déclaration SACEM" },
      { id:"s3_5c", label:"Conserver la confirmation dans le dossier concert" },
    ]},
    { id:"s3_6", label:"Confirmation du mandataire reçue", hint:"Date, heure, durée, format revalidés + salle d'échauffement + sono ok." },
  ]},
  { id:"s4", num:"Étape 4", title:"Communication interne", items:[
    { id:"s4_1", label:"Mail récap envoyé", hint:"Dans la semaine du concert : vérifier Moodle puis envoyer avec date, heure RDV, lieu, matériel, spécificités." },
  ]},
];

const COTECH_OPTIONS = [
  { val:"np", label:"Pas pertinent" },
  { val:"direct", label:"Contact direct CoTech" },
  { val:"passage", label:"Passage d'information" },
];

let saveTimer = null;

function scheduleSave() {
  clearTimeout(saveTimer);
  setIndicator('saving');
  saveTimer = setTimeout(doSave, 1200);
}

function setIndicator(state) {
  const el = document.getElementById('save-indicator');
  el.className = 'save-indicator ' + state;
  el.textContent = state==='saving' ? 'Sauvegarde…' : state==='saved' ? '✓ Sauvegardé' : '—';
}

async function doSave() {
  const progress = computeProgress().pct;
  try {
    await fetch('save.php', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        id: CONCERT.id,
        name: document.getElementById('meta-nom').value,
        date: document.getElementById('meta-date').value,
        respo: document.getElementById('meta-respo').value,
        mandataire: document.getElementById('meta-mandataire').value,
        state: S, progress,
      })
    });
    setIndicator('saved');
    const nom = document.getElementById('meta-nom').value.trim();
    document.title = nom ? `CONAN — ${nom}` : 'CONAN — Concert';
    document.getElementById('header-title').textContent = nom || 'Concert sans nom';
  } catch(e) { setIndicator(''); }
}

function toggleCheck(id) {
  S[id] = !S[id];
  const box = document.querySelector(`[data-check="${id}"]`);
  const lbl = document.querySelector(`[data-clabel="${id}"]`);
  if (box) box.classList.toggle('checked', !!S[id]);
  if (lbl) lbl.classList.toggle('done', !!S[id]);
  updateProgress(); updateStepDone(); scheduleSave();
}

function setYN(id, val) {
  S['yn_'+id] = val;
  const subs = document.getElementById('subs_'+id);
  const btns = document.querySelectorAll(`[data-ynb="${id}"]`);
  if (subs) subs.classList.toggle('visible', val==='y');
  btns.forEach(b => {
    b.classList.remove('active-yes','active-neutral');
    if (b.dataset.ynval===val) b.classList.add(val==='y'?'active-yes':'active-neutral');
  });
  updateProgress(); updateStepDone(); scheduleSave();
}

function setCotechMode(val) {
  S['cotech_mode'] = val;
  const btns = document.querySelectorAll('[data-cotech-btn]');
  btns.forEach(b => {
    b.classList.remove('active-yes','active-neutral');
    if (b.dataset.cotechBtn===val) b.classList.add(val==='passage'?'active-yes':'active-neutral');
  });
  const block = document.getElementById('cotech-passage-block');
  if (block) block.style.display = val==='passage' ? 'block' : 'none';
  updateProgress(); updateStepDone(); scheduleSave();
}

function renderCotech() {
  const mode = S['cotech_mode'] || null;
  const checked = !!S['cotech_transmis'];
  return `
    <div class="yesno-item">
      <div style="margin-bottom:.35rem">
        <span class="yesno-label">CoTech au courant</span>
        <div class="yesno-hint">Via #Conantech</div>
      </div>
      <div class="yesno-btns" style="margin-top:.5rem">
        ${COTECH_OPTIONS.map(o=>`
          <button class="yn-btn ${mode===o.val?(o.val==='passage'?'active-yes':'active-neutral'):''}"
            data-cotech-btn="${o.val}" onclick="setCotechMode('${o.val}')">${o.label}</button>
        `).join('')}
      </div>
    </div>
    <div id="cotech-passage-block" class="sub-items ${mode==='passage'?'visible':''}"
      style="display:${mode==='passage'?'block':'none'}">
      <div style="padding:.75rem 1rem">
        <div style="font-size:.83rem;font-weight:600;color:var(--ink);margin-bottom:.3rem">Éléments demandés par CoTech</div>
        <div class="yesno-hint" style="margin-bottom:.5rem">Inscrire les questions de CoTech, rajouter les réponses quand on les a.</div>
        <textarea class="text-field-area" placeholder="Questions et réponses…"
          oninput="S['cotech_text']=this.value;scheduleSave()"
        >${S['cotech_text']||''}</textarea>
        <div class="text-field-done-row">
          <div class="check-wrap" onclick="toggleCheck('cotech_transmis')">
            <div class="check-box ${checked?'checked':''}" data-check="cotech_transmis"></div>
          </div>
          <span class="text-field-done-label ${checked?'done':''}" data-clabel="cotech_transmis"
            onclick="toggleCheck('cotech_transmis')">Transmis</span>
        </div>
      </div>
    </div>`;
}

function renderItem(it) {
  if (it.type==='cotech') return renderCotech();
  if (it.type==='textfield') {
    const checked = !!S['tf_'+it.id];
    return `<div class="item"><div class="item-content">
      <div class="item-label">${it.label}</div>
      <div class="text-field-wrap">
        <textarea class="text-field-area" placeholder="${it.placeholder||''}"
          oninput="S['tft_${it.id}']=this.value;scheduleSave()"
        >${S['tft_'+it.id]||''}</textarea>
        <div class="text-field-done-row">
          <div class="check-wrap" onclick="toggleCheck('tf_${it.id}')">
            <div class="check-box ${checked?'checked':''}" data-check="tf_${it.id}"></div>
          </div>
          <span class="text-field-done-label ${checked?'done':''}" data-clabel="tf_${it.id}"
            onclick="toggleCheck('tf_${it.id}')">Transmis</span>
        </div>
      </div>
    </div></div>`;
  }
  if (it.type==='yesno') {
    const yn = S['yn_'+it.id]||null;
    const subsHtml = (it.subs||[]).map(s=>{
      const c=!!S[s.id];
      return `<div class="sub-item">
        <div class="sub-check ${c?'checked':''}" data-check="${s.id}" onclick="toggleCheck('${s.id}')"></div>
        <span class="sub-label ${c?'done':''}" data-clabel="${s.id}" onclick="toggleCheck('${s.id}')">${s.label}</span>
      </div>`;
    }).join('');
    return `
      <div class="yesno-item"><div class="yesno-row">
        <span class="yesno-label">${it.label}</span>
        <span class="yesno-question">Pertinent ?</span>
        <div class="yesno-btns">
          <button class="yn-btn ${yn==='y'?'active-yes':''}" data-ynb="${it.id}" data-ynval="y" onclick="setYN('${it.id}','y')">Oui</button>
          <button class="yn-btn ${yn==='n'?'active-neutral':''}" data-ynb="${it.id}" data-ynval="n" onclick="setYN('${it.id}','n')">Non</button>
        </div>
      </div></div>
      <div class="sub-items ${yn==='y'?'visible':''}" id="subs_${it.id}">${subsHtml}</div>`;
  }
  const c=!!S[it.id];
  return `<div class="item"><div class="item-row">
    <div class="check-wrap" onclick="toggleCheck('${it.id}')">
      <div class="check-box ${c?'checked':''}" data-check="${it.id}"></div>
    </div>
    <div class="item-content">
      <div class="item-label ${c?'done':''}" data-clabel="${it.id}" onclick="toggleCheck('${it.id}')">${it.label}</div>
      ${it.hint?`<div class="item-hint">${it.hint}</div>`:''}
    </div>
  </div></div>`;
}

function isCotechDone() {
  const mode=S['cotech_mode'];
  if (!mode) return false;
  if (mode==='passage') return !!S['cotech_transmis'];
  return true;
}

function isStepDone(step) {
  return step.items.every(it=>{
    if (it.type==='cotech') return isCotechDone();
    if (it.type==='textfield') return !!S['tf_'+it.id];
    if (it.type==='yesno') {
      if (!S['yn_'+it.id]) return false;
      if (S['yn_'+it.id]==='y') return (it.subs||[]).every(s=>!!S[s.id]);
      return true;
    }
    return !!S[it.id];
  });
}

function updateStepDone() {
  STEPS.forEach(step=>{
    const el=document.getElementById('step_'+step.id);
    if (el) el.classList.toggle('completed', isStepDone(step));
  });
}

function computeProgress() {
  let total=0, done=0;
  STEPS.forEach(step=>step.items.forEach(it=>{
    if (it.type==='cotech') { total++; if(isCotechDone()) done++; }
    else if (it.type==='textfield') { total++; if(S['tf_'+it.id]) done++; }
    else if (it.type==='yesno') {
      total++; if(S['yn_'+it.id]) done++;
      if(S['yn_'+it.id]==='y') (it.subs||[]).forEach(s=>{total++;if(S[s.id])done++;});
    } else { total++; if(S[it.id]) done++; }
  }));
  return { total, done, pct: total ? Math.round(done/total*100) : 0 };
}

function updateProgress() {
  const {total,done,pct}=computeProgress();
  document.getElementById('prog-fill').style.width=pct+'%';
  document.getElementById('prog-text').textContent=`${done} / ${total}`;
}

function render() {
  document.getElementById('steps').innerHTML = STEPS.map(step=>`
    <div class="step ${isStepDone(step)?'completed':''} ${step.parallel?'parallel':''} open" id="step_${step.id}">
      <div class="step-header" onclick="this.parentElement.classList.toggle('open')">
        <span class="step-num">${step.num}</span>
        <span class="step-title">${step.title}</span>
        ${step.parallel?'<span class="step-badge">parallèle</span>':''}
        <span class="step-chevron">▼</span>
      </div>
      <div class="step-body">${step.items.map(renderItem).join('')}</div>
    </div>`).join('');

  updateProgress(); updateStepDone();

  const fields={'meta-nom':CONCERT.name,'meta-date':CONCERT.date,'meta-respo':CONCERT.respo,'meta-mandataire':CONCERT.mandataire};
  Object.entries(fields).forEach(([id,val])=>{
    const el=document.getElementById(id);
    if (el&&val) el.value=val;
    if (el) el.addEventListener('input', scheduleSave);
  });
  if (CONCERT.name) document.title=`CONAN — ${CONCERT.name}`;
}

render();
</script>
</body>
</html>
