import numpy as np
import pandas as pd
import random
import math

random.seed(42)
np.random.seed(42)

# Plages calibrées approximativement sur des stats AIS réelles (vitesse/heading)
SPEED_NORMAL_MIN = 8
SPEED_NORMAL_MAX = 20
HEADING_STD_NORMAL = 5

SPEED_DEGASSING_MIN = 0.5
SPEED_DEGASSING_MAX = 4
HEADING_STD_DEGASSING = 40


def generate_normal_trajectory():
    lat = random.uniform(32.0, 38.0)
    lon = random.uniform(7.5, 12.0)
    heading = random.uniform(0, 360)
    speed = random.uniform(SPEED_NORMAL_MIN, SPEED_NORMAL_MAX)

    points = []
    for _ in range(13):
        heading += random.uniform(-HEADING_STD_NORMAL, HEADING_STD_NORMAL)
        heading %= 360
        step = 0.005 * (speed / 15)
        lat += step * math.cos(math.radians(heading))
        lon += step * math.sin(math.radians(heading))
        points.append({"lat": lat, "lon": lon, "speed": speed, "heading": heading})

    return points, round(random.uniform(0.0, 0.2), 3)


def generate_degassing_trajectory():
    lat = random.uniform(32.0, 38.0)
    lon = random.uniform(7.5, 12.0)
    heading = random.uniform(0, 360)
    speed = random.uniform(SPEED_DEGASSING_MIN, SPEED_DEGASSING_MAX)

    points = []
    for _ in range(13):
        heading += random.uniform(-HEADING_STD_DEGASSING, HEADING_STD_DEGASSING)
        heading %= 360
        step = 0.001
        lat += step * math.cos(math.radians(heading))
        lon += step * math.sin(math.radians(heading))
        points.append({"lat": lat, "lon": lon, "speed": speed, "heading": heading})

    return points, round(random.uniform(0.7, 1.0), 3)


def build_dataset(n_samples=3000):
    rows = []
    for _ in range(n_samples):
        category = random.choices(["normal", "degassing"], weights=[0.75, 0.25])[0]

        if category == "normal":
            points, anomaly = generate_normal_trajectory()
        else:
            points, anomaly = generate_degassing_trajectory()

        p_t10, p_t5, p_t, p_t30 = points[0], points[1], points[2], points[8]

        rows.append({
            "lat_t": p_t["lat"], "lon_t": p_t["lon"], "speed_t": p_t["speed"], "heading_t": p_t["heading"],
            "lat_t5": p_t5["lat"], "lon_t5": p_t5["lon"], "speed_t5": p_t5["speed"], "heading_t5": p_t5["heading"],
            "lat_t10": p_t10["lat"], "lon_t10": p_t10["lon"], "speed_t10": p_t10["speed"], "heading_t10": p_t10["heading"],
            "label_lat_t30": p_t30["lat"],
            "label_lon_t30": p_t30["lon"],
            "label_anomaly_score": anomaly,
            "category": category
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build_dataset(n_samples=3000)
    df.to_csv("dataset_training.csv", index=False)
    print(f"Dataset généré : {len(df)} lignes")
    print(df["category"].value_counts())