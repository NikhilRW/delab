import argparse
from operator import add

from pyspark.sql import SparkSession


def main():
    parser = argparse.ArgumentParser(description="Basic Spark RDD operations")
    parser.add_argument("--rows", type=int, default=1_000_000)
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be at least 1")

    spark = (
        SparkSession.builder
        .appName("Lab6-RDD-Operations")
        .master("local[2]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        # Generate (transaction_id, amount) records across four partitions.
        # Amounts repeat from 1 to 1000; no large Python list or CSV is needed.
        transactions = spark.sparkContext.range(
            1, args.rows + 1, numSlices=4
        ).map(lambda transaction_id: (transaction_id, (transaction_id - 1) % 1000 + 1))

        # MAP: extract the amount from each transaction.
        amounts = transactions.map(lambda transaction: transaction[1]).cache()
        print(f"Records: {args.rows}")
        print(f"Partitions: {amounts.getNumPartitions()}")
        print(f"MAP - first 5 amounts: {amounts.take(5)}")

        # FILTER: keep transactions whose amount is greater than 500.
        large_amounts = amounts.filter(lambda amount: amount > 500)
        print(f"FILTER - amounts > 500: {large_amounts.count()}")

        # REDUCE: combine all amounts into one total.
        total = amounts.reduce(add)
        print(f"REDUCE - total amount: {total}")

        # AGGREGATE: compute count and sum within partitions, then combine them.
        count, amount_sum = amounts.aggregate(
            (0, 0),
            lambda result, amount: (result[0] + 1, result[1] + amount),
            lambda left, right: (left[0] + right[0], left[1] + right[1]),
        )
        print(f"AGGREGATE - count: {count}, sum: {amount_sum}")
        print(f"Average amount: {amount_sum / count:.2f}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
