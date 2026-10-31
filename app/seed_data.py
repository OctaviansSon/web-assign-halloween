"""Sample data. Plain Python (no imports), so it can be reused by the seed script, tests and docs."""

CRIMINALS = [
    {
        "nickname": "Crimson Comet", "name": "Viktor Hale", "reward": 120000,
        "latitude": 35.6895, "longitude": 139.6917, "location_note": "Seen at the Neo-Tokyo orbital docks",
        "difficulty": 9, "armed": True, "has_crew": True, "escape_master": True,
    },
    {
        "nickname": "Dr. Nebula", "name": "Elena Voss", "reward": 85000,
        "latitude": None, "longitude": None, "location_note": "Last seen in the Ganymede Station black market",
        "difficulty": 7, "armed": False, "has_crew": True, "escape_master": True,
    },
    {
        "nickname": "Lazy Jack", "name": None, "reward": 3500,
        "latitude": -33.8688, "longitude": 151.2093, "location_note": None,
        "difficulty": 2, "armed": False, "has_crew": False, "escape_master": False,
    },
    {
        "nickname": "Iron Mama", "name": "Magda Orlov", "reward": 45000,
        "latitude": None, "longitude": None, "location_note": "Hiding in a mining colony on Callisto",
        "difficulty": 6, "armed": True, "has_crew": True, "escape_master": False,
    },
    {
        "nickname": "Silent Rook", "name": None, "reward": 22000,
        "latitude": 64.1466, "longitude": -21.9426, "location_note": None,
        "difficulty": 8, "armed": True, "has_crew": False, "escape_master": True,
    },
    {
        "nickname": "Fast Eddie Zero", "name": "Eduardo Quill", "reward": 7500,
        "latitude": 19.4326, "longitude": -99.1332, "location_note": None,
        "difficulty": 4, "armed": False, "has_crew": False, "escape_master": True,
    },
    {
        "nickname": "The Pale Baker", "name": "Anton Kessler", "reward": 15000,
        "latitude": None, "longitude": None, "location_note": "Orbiting bakery-ship 'Rye Moon'",
        "difficulty": 3, "armed": False, "has_crew": True, "escape_master": False,
    },
    {
        "nickname": "Madame Static", "name": None, "reward": 60000,
        "latitude": -1.2921, "longitude": 36.8219, "location_note": "Broadcasting from a pirate radio relay",
        "difficulty": 7, "armed": True, "has_crew": True, "escape_master": True,
    },
]

# (criminal nickname, success, notes, days ago)
HUNTS = [
    ("Crimson Comet", False, "Target escaped through an asteroid field.", 28),
    ("Crimson Comet", False, "Lost him after he jumped through a hyperspace gate.", 20),
    ("Crimson Comet", False, "Ambushed by his crew near Titan, our ship was damaged.", 9),
    ("Dr. Nebula", False, "Tracked her to a lab station, but it was empty and booby-trapped.", 25),
    ("Dr. Nebula", True, "Captured after her shuttle ran out of fuel near Europa.", 3),
    ("Lazy Jack", True, "Found asleep in a noodle bar. Easiest bounty ever.", 22),
    ("Iron Mama", False, "Her crew outgunned us at the mining camp, we had to retreat.", 17),
    ("Iron Mama", False, "An informant sold us out and the colony was evacuated.", 6),
    ("Silent Rook", False, "He vanished before the stakeout even began.", 15),
    ("Silent Rook", True, "Cornered in a cargo bay, surrendered without a fight.", 2),
    ("Fast Eddie Zero", False, "Outran our ship in a stolen racing pod.", 12),
    ("The Pale Baker", True, "Arrested while delivering fresh bread to the docks.", 11),
    ("Madame Static", False, "Our comms were jammed and we lost the target.", 7),
    ("Madame Static", False, "Found the pirate radio relay, but only a looping recording was left.", 1),
]
