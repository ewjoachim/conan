# CONAN — Déploiement

## Structure des fichiers

```
conan/
├── Dockerfile         → Image PHP/Apache
├── conan.container    → Podman Quadlet (systemd unit)
├── index.php          → Page d'accueil (liste des concerts)
├── new.php            → Création d'un nouveau concert
├── .htaccess          → Routage des URLs
├── concert/
│   ├── index.php      → Checklist d'un concert
│   └── save.php       → API de sauvegarde
└── data/
    └── concerts.json  → Données (créé automatiquement)
```

## Déploiement via Podman Quadlet

### 1. Builder l'image
```bash
podman build -t conan:latest .
```

### 2. Préparer le volume de données sur l'hôte
```bash
mkdir -p /opt/conan/data
chmod 775 /opt/conan/data
```

### 3. Déployer le Quadlet
Copier `conan.container` dans le dossier Quadlet approprié :
```bash
# Pour un service système
cp conan.container /etc/containers/systemd/

# Ou pour un service utilisateur
cp conan.container ~/.config/containers/systemd/
```

### 4. Recharger et démarrer
```bash
systemctl daemon-reload
systemctl start conan
# ou pour un service utilisateur :
systemctl --user daemon-reload
systemctl --user start conan
```

### 5. Vérifier
```bash
systemctl status conan
podman logs conan
```

## Notes

- Les données sont stockées dans `/opt/conan/data/concerts.json` sur l'hôte
- Le conteneur écoute sur le port **8080** → à proxyfier vers `conan.negitachi.fr`
- Le flag `:Z` sur le volume gère le contexte SELinux automatiquement
- PHP 8.2, Apache avec mod_rewrite
