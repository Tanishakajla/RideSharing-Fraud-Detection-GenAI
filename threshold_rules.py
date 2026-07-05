"""
Hard-coded threshold rules, mirroring the numbers written in knowledge_base/*.md.
This is intentionally simple Python logic, NOT the LLM - math and comparisons
belong here, where they're guaranteed correct, not in the prompt.

If you ever update a threshold in a .md file, update it here too - these two
should always stay in sync.
"""

def check_velocity_fraud(trip: dict) -> str:
    trips_1h = trip["user_trips_last_1h"]
    if trips_1h >= 7:
        return "high"
    elif trips_1h >= 4:
        return "moderate"
    return "none"


def check_device_sharing_fraud(trip: dict) -> str:
    if trip["num_users_on_device"] >= 5 or trip["device_degree"] >= 5:
        return "high"
    return "none"


def check_card_testing_fraud(trip: dict) -> str:
    if trip["card_degree"] >= 4:
        return "high"
    return "none"


def check_new_account_fraud(trip: dict) -> str:
    if trip["seconds_since_signup"] < 600 and trip["user_trips_last_1h"] >= 2:
        return "high"
    elif trip["seconds_since_signup"] < 600:
        return "moderate"
    return "none"


def evaluate_all_thresholds(trip: dict) -> dict:
    """Returns a verified, pre-computed suspicion level for each fraud pattern.
    This is the ground truth the LLM will be told to use, instead of
    calculating it itself."""
    return {
        "velocity_fraud": check_velocity_fraud(trip),
        "device_sharing_fraud": check_device_sharing_fraud(trip),
        "card_testing_fraud": check_card_testing_fraud(trip),
        "new_account_fraud": check_new_account_fraud(trip)
    }


if __name__ == "__main__":
    test_trip = {
        "fare": 5.0,
        "seconds_since_signup": 90,
        "user_trip_count": 1,
        "user_trips_last_1h": 6,
        "num_users_on_device": 4,
        "device_degree": 7,
        "card_degree": 3
    }
    print(evaluate_all_thresholds(test_trip))