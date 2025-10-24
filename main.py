import random
import psycopg2
import requests

BASE_URL = "https://randomuser.me/api/?nat=us,dk,fr,gb"
PARTIES = [
    "Parti Tech Pour Tous (PTPT)",
    "Le Parti du Retour (PR)",
    "Mouvement des Affaires Numériques",
    "Forces Nouvelles du Numérique (FNN)",
    "Rassemblement des Data Scientists (RDS)",
    "Union Pour le Full Stack (UPFS)",
    "Parti Cloud Souverain (PCS)",
]

random.seed(42)  

#def generate_voters(num_voters):

def get_postgres_connection():
    try:
        conn = psycopg2.connect("host=localhost dbname=voting user=postgres password=postgres port=5432")
        
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
    
def create_votes_table(con, cur):
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS candidates (
        candidate_id SERIAL PRIMARY KEY,
        candidate_name VARCHAR(100) NOT NULL,
        party VARCHAR(100) NOT NULL,
        biography TEXT,
        campaign_promises TEXT,
        photo_url TEXT   
       
    );
    
    cREATE TABLE IF NOT EXISTS voters (
        voter_id SERIAL PRIMARY KEY,
        voter_name VARCHAR(100),
        date_of_bd DATE,
        gender VARCHAR(10),
        nationality VARCHAR(50),
        registration_number VARCHAR(50) UNIQUE,
        address TEXT,
        email VARCHAR(100) UNIQUE,
        phone_number VARCHAR(15) UNIQUE,
        picture_url TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    create TABLE IF NOT EXISTS votes (
        vote_id SERIAL,
        voter_id INT REFERENCES voters(voter_id),
        candidate_id INT REFERENCES candidates(candidate_id),
        vote_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (vote_id, voter_id)
        );
        
    '''
    cur.execute(create_table_query)
    con.commit()

def insert_sample_data(con, cur):

    query = '''
    INSERT INTO candidates (candidate_name, party, biography, campaign_promises, photo_url) VALUES
    ('Kiswendsida Ulrich O.', 'Parti Tech Pour Tous (PTPT)', 
     'Jeune ingénieur data passionné par la tech et l''innovation. Expert Kafka et Spark cherchant à révolutionner la politique avec des algorithmes.', 
     'Promesses: WiFi gratuit partout, Python obligatoire à l''école, déploiement de Kafka dans tous les ministères, bugs fixés en 24h max',
     './images/moi.jpg'),
     
    ('Laurent Ba-Code', 'Le Parti du Retour (PR)', 
     'Ancien dirigeant nostalgique du bon vieux temps. Expert en comebacks politiques multiples.',
     'Promesses: Retour aux sources, recalcul des votes de 2010, infrastructure cloud souveraine',
     './images/candidate1.jpg'),
     
    ('Tidiane Tech', 'Mouvement des Affaires Numériques (MAN)', 
     'Banquier reconverti dans la fintech. Spécialiste des transactions haute fréquence.',
     'Promesses: Blockchain pour tous, Crypto nationale, Digital banking obligatoire',
     './images/candidate2.jpg'),
     
    ('Guillaume So-Code', 'Forces Nouvelles du Numérique (FNN)', 
     'Jeune leader tech du Nord. Rebelle devenu entrepreneur.',
     'Promesses: Startups dans chaque ville, Incubateurs publics, Tax break pour devs',
     './images/candidate3.jpg'),
     
    ('Alassane O-Data', 'Rassemblement des Data Scientists (RDS)', 
     'Économiste devenu data scientist. Spécialiste des modèles prédictifs.',
     'Promesses: Open data obligatoire, IA dans l''administration, Dashboard national temps réel',
     './images/candidate4.jpg'),
     
    ('Simone Ba-Stack', 'Union Pour le Full Stack (UPFS)', 
     'Développeuse full-stack féministe. Première femme candidate geek.',
     'Promesses: Parité dans la tech, Code camps pour femmes, Quotas de dev féminines',
     './images/candidate5.jpg'),
     
    ('IB O-Cloud', 'Parti Cloud Souverain (PCS)', 
     'Expert DevOps de Nasso. Partisan du cloud souverain africain.',
     'Promesses: Datacenters africains, Souveraineté numérique, Cloud Act africain',
     './images/candidate6.jpg');
    '''
    cur.execute(query)
    con.commit()
    
def generate_voters(num_voters):
    voters = []
    for _ in range(num_voters):
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()['results'][0]
            voter = {
                'name': f"{data['name']['first']} {data['name']['last']}",
                'date_of_bd': data['dob']['date'][:10],
                'gender': data['gender'],
                'nationality': data['nat'],
                'registration_number': data['login']['uuid'],   
                'address': f"{data['location']['street']['number']} {data['location']['street']['name']}, {data['location']['city']}, {data['location']['state']}, {data['location']['country']}, {data['location']['postcode']}",
                'email': data['email'],
                'phone_number': data['phone'],
                'picture_url': data['picture']['large'],
            }
            voters.append(voter)

if __name__ == "__main__":
     conn = get_postgres_connection()
     if conn:
         cur = conn.cursor()
         create_votes_table(conn, cur)
         cur.execute("SELECT COUNT(*) FROM candidates;")
         count = cur.fetchone()[0]
         if count == 0:
            insert_sample_data(conn, cur)
        
         count = cur.execute("SELECT COUNT(*) FROM voters;").fetchone()[0]
         if count == 0:
            voters = generate_voters(5000)
            for voter in voters:
                insert_query = '''
                INSERT INTO voters (voter_name, date_of_bd, gender, nationality, registration_number, address, email, phone_number, picture_url) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                '''
                cur.execute(insert_query, (
                    voter['name'],
                    voter['date_of_bd'],
                    voter['gender'],    
                    voter['nationality'],
                    voter['registration_number'],   
                    voter['address'],
                    voter['email'],
                    voter['phone_number'],
                    voter['picture_url']
                ))
            conn.commit()
        
         cur.close()
         conn.close()
         