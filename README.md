# 🌱 MIFFA

> *Garder le lien, préserver la mémoire, célébrer ce qui nous unit.*


![Aperçu de Miffa](images_Readme/miffa.png)

MIFFA est une application web fullstack dédiée à la gestion de réseaux familiaux et amicaux. Elle permet à chaque famille de créer son propre espace privé, de gérer ses membres, de visualiser ses liens, de partager des souvenirs et de rester connectée — en temps réel.

---

## ✨ Fonctionnalités

### 👥 Gestion des membres & familles
- Création et gestion de familles (architecture **multi-tenant**)
- Système de rôles : **Administrateur**, **Membre**, **Visiteur**
- Demandes d'adhésion et validation par l'admin
- Profils personnalisés avec photo, biographie et date de naissance

![Aperçu de la gestion des membres](images_Readme/gestion_membres.png)
![Aperçu de la section membres](images_Readme/membres.png)

### 🌳 Arbre généalogique
- Visualisation interactive des liens familiaux
- Algorithme **BFS (Breadth-First Search)** pour la traversée et l'affichage des relations
- Définition des liens entre membres (parent, enfant, conjoint, etc.)

![Aperçu de l'arbre généalogique](images_Readme/arbre.png)


### 📰 Fil d'actualité
- Publication et partage d'annonces familiales
- Interactions entre membres de la famille

![Aperçu de la fil d'actualités](images_Readme/fil.png)


### 🖼️ Médiathèque
- Upload et gestion de photos, vidéos et documents
- Stockage via **Cloudinary**

![Aperçu de la médiathèque](images_Readme/media.png)


### 📅 Calendrier
- Événements familiaux partagés
- Rappels et anniversaires

![Aperçu du Calendrier](images_Readme/calendrier.png)


### ⏳ Chronologie
- Histoire et événements familiaux classés dans le temps

![Aperçu de la chronologie](images_Readme/chrono.png)


### ⚡ Temps réel
- Notifications et mises à jour en temps réel via **Django Channels** et **WebSocket**

![Aperçu des Notifications](images_Readme/notif.png)


---

## 🛠️ Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python, Django |
| Temps réel | Django Channels, WebSocket |
| Base de données | PostgreSQL |
| Stockage médias | Cloudinary |
| Frontend | HTML, CSS, JavaScript |
| Auth | Django Authentication |
| Déploiement | Docker (optionnel) |

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- PostgreSQL
- Un compte Cloudinary
- Redis (pour Django Channels)

### Cloner le projet
```bash
git clone https://github.com/Delprogram/MIFFA.git
cd MIFFA
```

### Environnement virtuel
```bash
python -m venv env
source env/bin/activate  # Windows : env\Scripts\activate
pip install -r requirements.txt
```

### Variables d'environnement
Crée un fichier `.env` à la racine :
```env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/miffa
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
REDIS_URL=redis://localhost:6379
```

### Base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Lancer le serveur
```bash
python manage.py runserver
```

---

## 📁 Structure du projet

```
MIFFA/
├── accounts/          # Gestion des utilisateurs et authentification
├── families/          # Gestion des familles et membres
├── tree/              # Arbre généalogique (BFS)
├── feed/              # Fil d'actualité
├── media_app/         # Médiathèque
├── calendar_app/      # Calendrier
├── timeline/          # Chronologie
├── static/            # Fichiers statiques
├── templates/         # Templates HTML
├── miffa/             # Configuration Django
└── requirements.txt
```

---

## 🎓 Contexte

Projet fullstack développé et présenté en soutenance dans le cadre du **Bachelor Développeur Web Fullstack** à **CODA Orléans**.

---

## 👤 Auteur

**Fidel AHOUANHOU**
- 🌐 [Portfolio](https://delprogram.github.io/Portfolio/)
- 💼 [LinkedIn](https://www.linkedin.com/in/fidel-ahouanhou-687286398/)
- 🐙 [GitHub](https://github.com/Delprogram)
- 📧 fidelahouanhou@gmail.com

---

> *"Transformer une idée en quelque chose qui tourne vraiment est, pour moi, l'une des satisfactions les plus concrètes qui soit."*
