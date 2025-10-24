import pyspark
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from pyspark.sql.functions import sum as spark_sum
from pyspark.sql import functions as F

import os
jar_path = os.path.join(os.path.dirname(__file__), "postgresql-42.7.8.jar")

if __name__ == "__main__":

    spark = pyspark.sql.SparkSession.builder.appName("real time voting eng")\
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7")\
            .config("spark.jars",jar_path)\
            .config("spark.sql.adaptive.enabled", "false")\
            .config("spark.hadoop.io.native.lib.available", "false")\
            .getOrCreate()
        
    vote_schema = StructType([
            StructField("candidate_name", StringType(), True),
            StructField("candidate_id", IntegerType(), True),
            StructField("voting_time", TimestampType(), True),
            StructField("voter_name", StringType(), True),
            StructField("party", StringType(), True),
            StructField("biography", StringType(), True),
            StructField("campaign_promises", StringType(), True),
            StructField("photo_url", StringType(), True),
            StructField("date_of_bd", StringType(), True),
            StructField("gender", StringType(), True),
            StructField("nationality", StringType(), True),
            StructField("address", StringType(), True),
            StructField("email", StringType(), True),
            StructField("picture_url", StringType(), True),
            StructField("phone_number", StringType(), True),
            StructField("vote", IntegerType(), True),
        ])
        
    votes_df = spark \
            .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "localhost:9092") \
                .option("subscribe", "votes_topic") \
                .option("startingOffsets", "earliest") \
                .load()\
            .selectExpr("CAST(value AS STRING)")\
            .select(from_json(col("value"), vote_schema).alias("data"))\
            .select("data.*")
            
            
    votes_df = votes_df.withColumn("voting_time", col("voting_time").cast(TimestampType()))\
        .withColumn("vote", col("vote").cast(IntegerType()))
        
    enriched_votes_df = votes_df.withWatermark("voting_time", "1 minute")
                
            
    #aggregate votes per candidate every 5 minutes
    votes_per_candidates = enriched_votes_df.groupBy("candidate_id","candidate_name","photo_url","party","campaign_promises")\
        .agg(spark_sum('vote').alias('total_votes'))
    
    enriched_votes_df = enriched_votes_df.withColumn(
    "country",
    F.trim(F.element_at(F.split(F.col("address"), ","), -2))
)
        
    turnout_by_location_df = enriched_votes_df.groupBy("country").count().alias("total_votes")
    
    votes_per_candidate_to_kafka = votes_per_candidates.selectExpr('to_json(struct(*)) AS value') \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("topic", "aggregated_votes_per_candidate") \
.option("checkpointLocation",  "C:/spark_checkpoints/checkpoint1")\
        .outputMode("update") \
        .start()
        
    turnout_by_location_to_kafka = turnout_by_location_df.selectExpr('to_json(struct(*)) AS value') \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("topic", "aggregated_turnout_by_location") \
.option("checkpointLocation",  "C:/spark_checkpoints/checkpoint2")\
        .outputMode("update") \
        .start()
        
    votes_per_candidate_to_kafka.awaitTermination()
    turnout_by_location_to_kafka.awaitTermination()
    
    