# 🗳️ Real-Time Election Dashboard

> Système de vote en temps réel avec traitement streaming - Kafka, Spark & Streamlit

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Kafka](https://img.shields.io/badge/Kafka-3.0+-red.svg)](https://kafka.apache.org/)
[![Spark](https://img.shields.io/badge/Spark-3.5+-orange.svg)](https://spark.apache.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

##  Aperçu

![Dashboard Demo](./assets/demo.gif)

*Dashboard électoral en temps réel affichant les résultats instantanément*

---

##  Fonctionnalités

- ⚡ **Traitement en temps réel** - Des milliers de votes traités par seconde
- 📊 **Dashboard interactif** - Visualisation instantanée des résultats
- 🏆 **Podium dynamique** - Top 3 mis en avant avec photos
- 🌍 **Suivi géographique** - Participation par région
- 🔄 **Auto-refresh** - Mise à jour automatique toutes les 10 secondes
- 🐳 **Dockerisé** - Déploiement en une commande

---

##  Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   PostgreSQL│─────▶    producer  │─────▶│   Kafka    │─────▶│   spark    │
│   (Votes)   │      │  (Streams)  │      │ (Processing)│      │  (Storage)  │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                                                                        │
                                                                        ▼
                                                                 ┌─────────────┐
                                                                 │  Streamlit  │
                                                                 │ (Dashboard) │
                                                                 └─────────────┘
```

**Pipeline de données :**
1. **Ingestion** - Les votes sont envoyés à Kafka via un producteur Python
2. **Traitement** - Spark Structured Streaming agrège les données en temps réel
3. **Stockage** - PostgreSQL conserve les résultats et les métadonnées
4. **Visualisation** - Streamlit affiche le dashboard interactif

---

## 🛠️ Stack Technique

| Technologie | Usage |
|------------|-------|
| **Apache Kafka** | Event streaming & message broker |
| **Apache Spark** | Stream processing & aggregation |
| **Python** | Data engineering & scripting |
| **Streamlit** | Dashboard & visualisation |
| **PostgreSQL** | Database & persistence |
| **Docker** | Containerization & orchestration |

---

##  Quick Start

### Prérequis

- Docker & Docker Compose
- 8GB RAM minimum
- Ports disponibles : 9092, 5432, 8501

### Installation

```bash
# Cloner le repository
git clone https://github.com/oulrich-ops/realTimeVotinEng
cd real-time-voting

# Lancer tous les services
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### Accès au Dashboard

Ouvrez votre navigateur : **http://localhost:8501**



---

## 🎮 Usage

### Démarrer la simulation de votes

```bash
# Lancer le producteur de votes
docker-compose exec producer python vote_producer.py
```

### Visualiser les résultats

Le dashboard se met à jour automatiquement et affiche :
- **Top 3** - Podium des leaders avec photos
- **Tous les candidats** - Grille 3×N avec promesses de campagne
- **Statistiques** - Graphiques et métriques détaillées
- **Participation** - Taux calculé en temps réel

### Configurer le rafraîchissement

Dans le sidebar du dashboard :
- Ajustez l'intervalle de rafraîchissement (5-60 secondes)
- Cliquez sur "Rafraîchir" pour une mise à jour manuelle

---

## 📊 Données

### Base de données

Le système utilise PostgreSQL avec 3 tables principales :

**voters** - Électeurs inscrits
```sql
voter_id, name, email, registration_date
```

**candidates** - Candidats à l'élection
```sql
candidate_id, candidate_name, party, biography, campaign_promises, photo_url
```

**votes** - Votes enregistrés
```sql
vote_id, voter_id, candidate_id, timestamp, location
```

### Topics Kafka

- `votes` - Votes bruts
- `aggregated_votes_per_candidate` - Agrégation par candidat
- `aggregated_turnout_by_location` - Participation par région

---

##  Configuration

### Variables d'environnement

Créez un fichier `.env` :

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=voting
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### Ajuster les paramètres Spark

Modifiez `spark/streaming_job.py` :

```python
# Fenêtre d'agrégation
window_duration = "10 seconds"
slide_duration = "5 seconds"
```

---

##  Cas d'Usage

- **Élections** - Suivi en temps réel des résultats électoraux
- **Sondages** - Collecte et analyse instantanée de votes
- **Événements** - Vote du public lors de compétitions
- **Démocratie** - Plateformes de vote participatif

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

---

## 📝 Roadmap

- [ ] Ajouter l'authentification des électeurs
- [ ] Implémenter la détection de fraude ML
- [ ] Support multi-élections
- [ ] Export des résultats (PDF, Excel)
- [ ] API REST pour intégration externe
- [ ] Mode production avec Kubernetes

---

## 👨 Auteur

**Oulrich-ops**

- GitHub: [@oulrich-ops](https://github.com/oulrich-ops)
- LinkedIn: [Kiswendsida](https://linkedin.com/in/o-kiswendsida)
- Email: votre.email@example.com

---

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

##  Remerciements

- Apache Kafka & Spark communities
- Streamlit team pour le framework de dashboard
- Toute la communauté open source

---

<div align="center">

**⭐ N'oubliez pas de mettre une étoile si ce projet vous a aidé ! ⭐**

Made with ❤️ and ☕ 

</div>