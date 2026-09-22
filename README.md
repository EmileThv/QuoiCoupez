# QuoiCoupez 🎬

**QuoiCoupez** est un logiciel de montage vidéo développé en Python avec **PySide6**, dans le cadre des ressources **R5.A.05 (Programmation avancée)** et **R5.A.06 (Sensibilisation à la programmation multimédia)** du BUT Informatique (semestre 5).

Inspiré d'outils comme CapCut, il permet de charger des vidéos, de les organiser sur une timeline multi-pistes, d'y appliquer des effets visuels et audio, de prévisualiser le montage en temps réel, puis d'exporter le résultat final.

## Fonctionnalités visées

- Chargement de vidéos (FFmpeg / OpenCV)
- Affichage d'une timeline multi-pistes (vidéo / audio)
- Affichage des miniatures et images-clés (keyframes)
- Ajout de pistes d'effets (vidéo et audio)
- Lecture (playback) du montage avec effets appliqués en temps réel
- Export de la vidéo finale

## Équipe

Projet développé par **Matthieu**, **Bastian**, **Élie** et **Émile**.

## Stack technique

- **Python 3** — langage principal
- **PySide6** — interface graphique (Qt for Python)
- **OpenCV** (`opencv-python`) — lecture des frames, miniatures, traitement d'image
- **FFmpeg** (via `ffmpeg-python`) — décodage/encodage et export vidéo
- **Audiomentations** — effets audio
- **PyFx** *(optionnel)* — effets visuels additionnels

## Installation

```bash
# Cloner le dépôt
git clone <url-du-depot>
cd PROJET_QUOICOUPEZ

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# Installer les dépendances
pip install -r requirements.txt
```

## Lancer l'application

```bash
python main.py
```

## Structure du projet

```
video_editor/
│
├── main.py                # Point d'entrée : lance QApplication et la fenêtre principale
├── requirements.txt        # Dépendances (PySide6, opencv-python, ffmpeg-python, audiomentations...)
│
├── ui/                     # Interface graphique (widgets Qt)
├── core/                   # Logique métier (Project, Clip, Track, TimelineModel)
├── video/                  # Traitement vidéo bas niveau (decoder, exporter, thumbnails)
├── effects/                # Effets vidéo et audio
├── workers/                # Threads Qt (lecture, export)
├── resources/               # Icônes, styles QSS
├── assets/                  # Médias de test / démonstration
└── tests/                   # Tests unitaires (core/ et effects/)
```

Chaque répertoire contient un fichier `info.txt` détaillant précisément son contenu et son rôle.

## Utilisation de Git

Quelques commandes usuelles pour travailler ensemble sur ce dépôt.

### Récupérer le projet et se mettre à jour

```bash
git clone <url-du-depot>     # Cloner le dépôt (une seule fois)
git pull                     # Récupérer les derniers changements de la branche courante
```

### Travailler sur une fonctionnalité

```bash
git checkout -b feature/nom-de-la-fonctionnalite   # Créer et se placer sur une nouvelle branche
git status                                          # Voir l'état des fichiers modifiés
git add chemin/vers/fichier.py                      # Ajouter un fichier précis au prochain commit
git commit -m "Ajoute la lecture des frames vidéo"  # Créer un commit avec un message clair
git push -u origin feature/nom-de-la-fonctionnalite # Envoyer la branche sur le dépôt distant
```

### Mettre à jour sa branche avec `main`

```bash
git checkout main
git pull
git checkout feature/nom-de-la-fonctionnalite
git merge main               # Intégrer les derniers changements de main dans sa branche
```

### Fusionner son travail

Une fois la fonctionnalité terminée et testée, ouvrir une **Pull Request** vers `main` (ou demander une revue à un binôme) plutôt que de merger directement, afin de garder `main` toujours fonctionnel.

### Bonnes pratiques

- Un commit = une modification cohérente et testée, avec un message explicite (à l'impératif : "Ajoute...", "Corrige...", "Refactore...").
- Ne jamais commiter directement de gros fichiers vidéo non nécessaires (voir `.gitignore`).
- Toujours faire `git pull` avant de commencer à travailler pour éviter les conflits.
- Une branche par fonctionnalité (`feature/...`) ou par correctif (`fix/...`).

## Répartition des tâches (7 semaines)

Le développement est découpé en 7 semaines avec une **progression incrémentale** : chaque semaine s'appuie sur les briques posées la semaine précédente. Un compte-rendu hebdomadaire doit être déposé sur Moodle décrivant les réalisations et les objectifs de la semaine suivante.

---

### Semaine 1 — Squelette du projet et modèle de données

**Objectif global :** avoir un projet qui se lance (fenêtre PySide6 vide) et les classes de données de base du montage, testées unitairement.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `main.py`, `ui/main_window.py`, `requirements.txt` | Initialiser le projet PySide6 (QApplication + QMainWindow vide), lister les dépendances dans `requirements.txt`, mettre en place l'arborescence des dossiers | `python main.py` ouvre une fenêtre vide fonctionnelle |
| **Bastian** | `core/project.py`, `core/track.py` | Créer la classe `Project` (état global : pistes, médias, durée) et la classe `Track` (liste de clips, type vidéo/audio) | Classes instanciables avec attributs de base, sans bug |
| **Élie** | `core/clip.py`, `core/timeline_model.py` | Créer la classe `Clip` (source, points in/out, position) et une première version de `TimelineModel` (ajout/suppression de clips) | On peut créer un `Project`, y ajouter une `Track`, et y ajouter un `Clip` en Python (script de test manuel) |
| **Émile** | `video/decoder.py`, `video/thumbnail.py` | Ouvrir une vidéo avec OpenCV, lire ses métadonnées (fps, durée, résolution, nombre de frames), générer une miniature (1 frame extraite) | Script qui affiche les métadonnées d'une vidéo de `assets/` et sauvegarde une miniature en image |

---

### Semaine 2 — Chargement et affichage d'une vidéo

**Objectif global :** pouvoir importer une vidéo et afficher ses frames dans l'interface.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `ui/preview_widget.py` | Créer le widget d'aperçu (QLabel + QImage), afficher une frame reçue depuis `video/decoder.py` | La première frame d'une vidéo test s'affiche dans la fenêtre principale |
| **Bastian** | `ui/media_library.py`, `video/thumbnail.py` | Lister les médias importés avec leur miniature (utiliser `video/thumbnail.py` d'Émile) | La bibliothèque affiche au moins une vidéo importée avec sa miniature |
| **Élie** | `workers/playback_worker.py` | Créer un `QThread` qui lit les frames d'une vidéo en boucle et émet un signal `Signal(QImage)` | Le thread tourne sans bloquer l'UI (test avec un print du numéro de frame) |
| **Émile** | `video/decoder.py` | Finaliser un décodeur itérable (frame par frame, respect du fps de la vidéo) | Le décodeur fournit une frame à la bonne cadence, utilisable par le `playback_worker` |

---

### Semaine 3 — Timeline statique et contrôles de lecture

**Objectif global :** afficher une timeline (pistes + clips) et pouvoir lire/mettre en pause une vidéo via des boutons.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `ui/timeline_widget.py` | Dessiner (via `paintEvent`) les pistes et les clips positionnés dessus, ainsi qu'une règle de temps | La timeline affiche au moins 2 pistes avec des clips statiques (couleurs/rectangles) |
| **Bastian** | `ui/controls_widget.py`, `ui/main_window.py` | Créer les boutons play/pause/stop et le slider de progression, les intégrer dans la fenêtre principale | L'utilisateur peut cliquer sur play/pause/stop, le slider avance pendant la lecture |
| **Élie** | `core/timeline_model.py` | Finaliser le modèle (déplacer, supprimer un clip) et émettre des signaux quand le modèle change | `timeline_widget.py` peut se redessiner automatiquement quand le modèle change |
| **Émile** | `workers/playback_worker.py` | Connecter le worker de lecture aux boutons play/pause/stop et au slider (seek) | La vidéo se lance, se met en pause et s'arrête correctement depuis l'UI |

---

### Semaine 4 — Interactivité de la timeline (drag & drop, découpe)

**Objectif global :** pouvoir glisser un média sur la timeline, sélectionner, déplacer et découper un clip.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `ui/timeline_widget.py` | Gérer les événements souris : sélection d'un clip, déplacement (drag) sur la piste | On peut sélectionner et déplacer un clip à la souris sur la timeline |
| **Bastian** | `ui/media_library.py`, `ui/timeline_widget.py` | Implémenter le drag & drop d'un média de la bibliothèque vers la timeline | Glisser une vidéo depuis la bibliothèque crée un nouveau clip sur la timeline |
| **Élie** | `core/clip.py`, `core/timeline_model.py` | Ajouter la découpe/le trim d'un clip (modification des points in/out), mise à jour du modèle | On peut raccourcir un clip depuis l'UI et la durée totale se met à jour |
| **Émile** | `video/thumbnail.py` | Générer plusieurs miniatures/keyframes par clip pour affichage dans les rectangles de la timeline | Les clips sur la timeline affichent une ou plusieurs vignettes représentatives |

---

### Semaine 5 — Système d'effets vidéo

**Objectif global :** poser l'architecture des effets et pouvoir appliquer un premier effet visuel à un clip.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `effects/base_effect.py`, `ui/effects_panel.py` | Créer la classe abstraite `Effect` (`apply(frame, params)`) et le panneau listant les effets disponibles avec leurs paramètres | Le panneau affiche la liste des effets et permet de choisir un effet pour un clip sélectionné |
| **Bastian** | `effects/video_effects.py` | Implémenter un effet de flou et un effet de correction colorimétrique (via OpenCV) | Les deux effets fonctionnent isolément sur une image de test |
| **Élie** | `effects/video_effects.py` | Implémenter l'incrustation de texte et l'incrustation d'image/logo sur une frame | Les deux effets fonctionnent isolément sur une image de test |
| **Émile** | `workers/playback_worker.py`, `core/clip.py` | Intégrer l'application des effets d'un clip pendant la lecture (pipeline frame → effets → affichage) | Un effet appliqué à un clip est visible en temps réel pendant la lecture |

---

### Semaine 6 — Effets audio et export vidéo

**Objectif global :** ajouter les effets audio et permettre l'export du montage final avec une barre de progression.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `video/exporter.py`, `workers/export_worker.py` | Implémenter l'export du montage (assemblage des clips + effets) via FFmpeg dans un `QThread` dédié | Un export basique (sans effets audio) produit un fichier vidéo valide |
| **Bastian** | `effects/audio_effects.py` | Créer le wrapper autour d'Audiomentations (gain, écho, réduction de bruit) | Au moins 2 effets audio fonctionnent isolément sur un fichier de test |
| **Élie** | `ui/main_window.py`, `workers/export_worker.py` | Créer la boîte de dialogue d'export et connecter le signal de progression à une barre de progression dans l'UI | La progression de l'export s'affiche en temps réel dans l'interface |
| **Émile** | `video/exporter.py` | Intégrer la piste audio (avec effets) dans l'export final aux côtés de la vidéo | Le fichier exporté contient l'image ET le son avec les effets appliqués |

---

### Semaine 7 — Finitions, tests et démonstration

**Objectif global :** stabiliser l'application, compléter les tests, soigner l'interface et préparer la vidéo de démonstration.

| Membre | Fichiers | Tâches | Objectif de fin de semaine |
|---|---|---|---|
| **Matthieu** | `resources/style.qss`, `resources/icons/` | Habiller l'application (style QSS, icônes sur les boutons), corriger les bugs UI remontés par l'équipe | Interface cohérente visuellement, sans bug bloquant connu |
| **Bastian** | `tests/test_effects.py` | Compléter les tests unitaires des effets vidéo et audio | Couverture de tests satisfaisante sur `effects/`, tests passants en CI locale |
| **Élie** | `tests/test_project.py` | Compléter les tests unitaires de `core/` (Project, Clip, Track, TimelineModel) | Couverture de tests satisfaisante sur `core/`, tests passants |
| **Émile** | `README.md`, vidéo de démonstration | Finaliser la documentation, préparer et enregistrer la vidéo de démonstration mettant en avant l'aspect multimédia | Vidéo de démo prête à être déposée sur Moodle |

---