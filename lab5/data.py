
import json
import random
import time
import os

os.makedirs("sensor_data", exist_ok=True)

for i in range(100):
    data = {
        "sensor_id": random.randint(1, 5),
        "temperature": round(
            random.uniform(20, 50), 2
        )
    }

    with open(
        f"sensor_data/data_{i}.json", "w"
    ) as f:
        json.dump(data, f)

    print("Generated:", data)
    time.sleep(2)
