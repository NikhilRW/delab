
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, DoubleType
)

spark = (
    SparkSession.builder
    .appName("SensorStreaming")
    .master("local[*]")
    .getOrCreate()
)

schema = StructType([
    StructField("sensor_id", IntegerType()),
    StructField("temperature", DoubleType())
])

df = (
    spark.readStream
    .schema(schema)
    .json("sensor_data")
)

result = df.withColumn(
    "status",
    (col("temperature") > 40)
)

query = (
    result.writeStream
    .format("console")
    .outputMode("append")
    .start()
)

query.awaitTermination()
