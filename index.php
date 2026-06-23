<?php
require_once __DIR__ . '/db.php';

$db = get_db();
$concerts = $db->query("SELECT * FROM concerts ORDER BY created_at DESC")->fetchAll();
?>
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CONAN — Négitachi</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Josefin+Sans:wght@400;600;700&display=swap');
:root {
  --green:#3a7d44;--green-dark:#2a5e32;--green-light:#d6edd9;--green-pale:#f4faf4;
  --green-mid:#eaf4eb;--white:#ffffff;--ink:#1a2e1d;--muted:#6b8c6e;--border:#c2ddc5;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Nunito',sans-serif;background:var(--green-pale);color:var(--ink);min-height:100vh;padding:0 0 4rem;}
.site-header{background:var(--green);padding:1.25rem 1.25rem 1rem;box-shadow:0 2px 12px rgba(30,69,38,.18);}
.header-inner{max-width:680px;margin:0 auto;}
.site-header h1{font-family:'Josefin Sans',sans-serif;font-weight:700;font-size:1.1rem;color:white;letter-spacing:.06em;text-transform:uppercase;}
.site-header h1 span{color:var(--green-light);font-weight:400;}
.site-header p{color:rgba(255,255,255,.65);font-size:.8rem;margin-top:.25rem;}
.main{max-width:680px;margin:2rem auto 0;padding:0 1rem;}
.top-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;flex-wrap:wrap;gap:.75rem;}
.section-title{font-family:'Josefin Sans',sans-serif;font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}
.btn-new{font-family:'Josefin Sans',sans-serif;font-size:.8rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:.55rem 1.25rem;background:var(--green);color:white;border:none;border-radius:6px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:.4rem;transition:background .15s;}
.btn-new:hover{background:var(--green-dark);}
.concert-list{display:flex;flex-direction:column;gap:.75rem;}
.concert-card{background:var(--white);border:1.5px solid var(--border);border-radius:8px;padding:1rem 1.125rem;text-decoration:none;color:var(--ink);display:flex;align-items:center;gap:1rem;transition:border-color .15s,box-shadow .15s;}
.concert-card:hover{border-color:var(--green);box-shadow:0 2px 8px rgba(58,125,68,.1);}
.concert-info{flex:1;min-width:0;}
.concert-name{font-family:'Josefin Sans',sans-serif;font-weight:700;font-size:1rem;letter-spacing:.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.concert-meta{font-size:.78rem;color:var(--muted);margin-top:.2rem;}
.concert-prog{display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;flex-shrink:0;}
.prog-pct{font-family:'Josefin Sans',sans-serif;font-size:.8rem;font-weight:700;color:var(--green);}
.prog-bar{width:72px;height:4px;background:var(--border);border-radius:2px;overflow:hidden;}
.prog-bar-fill{height:100%;background:var(--green);border-radius:2px;}
.empty-state{text-align:center;padding:3rem 1rem;color:var(--muted);}
.empty-state p{font-size:.9rem;margin-top:.5rem;}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(26,46,29,.5);z-index:200;align-items:center;justify-content:center;padding:1rem;}
.modal-overlay.open{display:flex;}
.modal{background:white;border-radius:10px;padding:1.5rem;width:100%;max-width:420px;box-shadow:0 8px 32px rgba(26,46,29,.2);}
.modal h2{font-family:'Josefin Sans',sans-serif;font-size:1rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin-bottom:1.25rem;}
.form-field{display:flex;flex-direction:column;gap:.25rem;margin-bottom:.875rem;}
.form-label{font-family:'Josefin Sans',sans-serif;font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600;}
.form-input{font-family:'Nunito',sans-serif;font-size:.9rem;border:1.5px solid var(--border);border-radius:6px;padding:.5rem .75rem;color:var(--ink);outline:none;transition:border-color .2s;width:100%;}
.form-input:focus{border-color:var(--green);}
.modal-actions{display:flex;gap:.75rem;justify-content:flex-end;margin-top:1.25rem;}
.btn-cancel{font-family:'Josefin Sans',sans-serif;font-size:.78rem;font-weight:600;padding:.5rem 1rem;border:1.5px solid var(--border);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer;}
.btn-cancel:hover{border-color:var(--ink);color:var(--ink);}
.btn-create{font-family:'Josefin Sans',sans-serif;font-size:.78rem;font-weight:700;padding:.5rem 1.25rem;background:var(--green);color:white;border:none;border-radius:6px;cursor:pointer;}
.btn-create:hover{background:var(--green-dark);}
</style>
</head>
<body>
<div class="site-header">
  <div class="header-inner">
    <h1>CONAN <span>/ Gestion des concerts</span></h1>
    <p>Négitachi — outil interne</p>
  </div>
</div>
<div class="main">
  <div class="top-bar">
    <span class="section-title"><?= count($concerts) ?> concert<?= count($concerts) > 1 ? 's' : '' ?></span>
    <button class="btn-new" onclick="document.getElementById('modal').classList.add('open')">+ Nouveau concert</button>
  </div>
  <div class="concert-list">
    <?php if (empty($concerts)): ?>
      <div class="empty-state"><div style="font-size:2rem">🎵</div><p>Aucun concert pour l'instant.<br>Crée le premier !</p></div>
    <?php else: ?>
      <?php foreach ($concerts as $c): ?>
        <?php $meta = array_filter([$c['date'], $c['respo']]); ?>
        <a class="concert-card" href="concert/<?= htmlspecialchars($c['id']) ?>">
          <div class="concert-info">
            <div class="concert-name"><?= htmlspecialchars($c['name'] ?: 'Concert sans nom') ?></div>
            <?php if ($meta): ?><div class="concert-meta"><?= htmlspecialchars(implode(' · ', $meta)) ?></div><?php endif; ?>
          </div>
          <div class="concert-prog">
            <span class="prog-pct"><?= $c['progress'] ?>%</span>
            <div class="prog-bar"><div class="prog-bar-fill" style="width:<?= $c['progress'] ?>%"></div></div>
          </div>
        </a>
      <?php endforeach; ?>
    <?php endif; ?>
  </div>
</div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="modal">
    <h2>Nouveau concert</h2>
    <form method="POST" action="new.php">
      <div class="form-field">
        <label class="form-label" for="name">Nom du concert</label>
        <input class="form-input" type="text" id="name" name="name" placeholder="Ex : Jonetachi 2025" required autofocus />
      </div>
      <div class="form-field">
        <label class="form-label" for="date">Date</label>
        <input class="form-input" type="text" id="date" name="date" placeholder="Ex : 15 mars 2025" />
      </div>
      <div class="form-field">
        <label class="form-label" for="respo">Respo Negi</label>
        <input class="form-input" type="text" id="respo" name="respo" placeholder="Prénom" />
      </div>
      <div class="modal-actions">
        <button type="button" class="btn-cancel" onclick="document.getElementById('modal').classList.remove('open')">Annuler</button>
        <button type="submit" class="btn-create">Créer →</button>
      </div>
    </form>
  </div>
</div>
</body>
</html>
