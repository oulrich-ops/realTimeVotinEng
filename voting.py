import datetime
import json
import random
import time as t
import psycopg2
from confluent_kafka import Consumer, SerializingProducer, KafkaError, KafkaException

def get_postgres_connection():
    try:
        conn = psycopg2.connect("host=localhost dbname=voting user=postgres password=postgres port=5432")
        
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
    
conf = {
    'bootstrap.servers': 'localhost:9092',
}

consumer = Consumer(conf | {
    'group.id': 'voter_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
})

producer = SerializingProducer(conf)

if __name__ == "__main__":
    

    conn = get_postgres_connection()
    if conn:
        cur = conn.cursor()
        candidate_query = cur.execute(
            """
            SELECT row_to_json(col)
            FROM (
                SELECT * FROM candidates
            ) AS col
            """
            )
        
        candidates= [candidate[0] for candidate in cur.fetchall()]
        
        if(len(candidates) == 0):
            raise Exception("No candidates found in the database.")
        
            
        consumer.subscribe(['voters_topic'])
        
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        raise KafkaException(msg.error())
                
                voter_data = json.loads(msg.value().decode('utf-8'))
                print("Sample voter data keys:", voter_data.keys())

                r = random.random()  

                if r > 0.70:
                    chosen_candidate = candidates[0]
                else:
                    chosen_candidate = random.choice(candidates)
                
                vote = voter_data | chosen_candidate | {
                    "voting_time": datetime.datetime.utcnow().isoformat(),
                    'vote': 1
                }
                
                try:
                    print(f"User {voter_data['registration_number']} voted for {chosen_candidate['candidate_name']}")
                    cur.execute(
                        """
                        INSERT INTO votes (voter_id, candidate_id, vote_timestamp)
                        VALUES (%s, %s, %s);
                        """,
                        (
                            voter_data['registration_number'],
                            chosen_candidate['candidate_id'],
                            vote['voting_time']
                        )
                    )
                    conn.commit()
                    
                    producer.produce(
                        topic="votes_topic",
                        key=voter_data["registration_number"],
                        value=json.dumps(vote),
                        on_delivery=lambda err, msg: print(f"Delivered vote for voter {msg.key()}" if err is None else f"Failed to deliver vote for voter {msg.key()}: {err}")
                    )
                    producer.poll(0)
                except Exception as e:
                    print(f"Error inserting vote for voter {voter_data['registration_number']}: {e}")
                t.sleep(0.5)               
        except KeyboardInterrupt:
                pass
                
                consumer.commit(msg)
        
        
        