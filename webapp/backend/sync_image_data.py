
from database import SessionLocal
from models import Resident, Completion

db = SessionLocal()

# Data from the image (2025-2026 year completions)
# CAR, ID, FLO, ICU, ED, NF (N), SWING (SW)
data = {
    # PGY-2s (PGY-1s in the image)
    "B. Perez": {"CARDIO": 1, "ID": 2, "FLOORS": 21, "ICU": 5, "ED": 0, "NF": 8, "SWING": 2},
    "L. Duarte": {"CARDIO": 2, "ID": 1, "FLOORS": 21, "ICU": 6, "ED": 0, "NF": 2, "SWING": 2},
    "J. Jhooty": {"CARDIO": 1, "ID": 1, "FLOORS": 17, "ICU": 8, "ED": 0, "NF": 8, "SWING": 0},
    "M. Artavia": {"CARDIO": 1, "ID": 2, "FLOORS": 19, "ICU": 4, "ED": 0, "NF": 8, "SWING": 4},
    "M. Delgadillo": {"CARDIO": 1, "ID": 1, "FLOORS": 17, "ICU": 4, "ED": 0, "NF": 2, "SWING": 8},
    "M. Cruz": {"CARDIO": 5, "ID": 0, "FLOORS": 21, "ICU": 8, "ED": 2, "NF": 8, "SWING": 1},
    "I. Estrada": {"CARDIO": 0, "ID": 1, "FLOORS": 21, "ICU": 7, "ED": 0, "NF": 2, "SWING": 1},
    "J. Cabrera": {"CARDIO": 1, "ID": 1, "FLOORS": 16, "ICU": 8, "ED": 0, "NF": 2, "SWING": 1},
    "M. Rivas": {"CARDIO": 2, "ID": 1, "FLOORS": 19, "ICU": 6, "ED": 0, "NF": 2, "SWING": 8},
    "R. Bernal": {"CARDIO": 2, "ID": 3, "FLOORS": 17, "ICU": 0, "ED": 0, "NF": 4, "SWING": 8},
    "A. Gonzalez": {"CARDIO": 4, "ID": 1, "FLOORS": 20, "ICU": 4, "ED": 0, "NF": 2, "SWING": 1},
    "N. Monroig": {"CARDIO": 1, "ID": 1, "FLOORS": 19, "ICU": 6, "ED": 0, "NF": 2, "SWING": 1},
    "C. Tucci": {"CARDIO": 1, "ID": 1, "FLOORS": 19, "ICU": 6, "ED": 0, "NF": 2, "SWING": 8},
    "L. Cordoba": {"CARDIO": 2, "ID": 1, "FLOORS": 8, "ICU": 6, "ED": 0, "NF": 2, "SWING": 1},

    # PGY-3s (PGY-2s in the image)
    "M. Garcia": {"CARDIO": 4, "ID": 3, "FLOORS": 27, "ICU": 13, "ED": 4, "NF": 8, "SWING": 3},
    "D. Cano": {"CARDIO": 4, "ID": 1, "FLOORS": 31, "ICU": 13, "ED": 4, "NF": 8, "SWING": 2},
    "K. Gonzalez": {"CARDIO": 3, "ID": 2, "FLOORS": 21, "ICU": 4, "ED": 4, "NF": 8, "SWING": 0},
    "C. Ayala": {"CARDIO": 1, "ID": 2, "FLOORS": 16, "ICU": 0, "ED": 0, "NF": 8, "SWING": 3},
    "K. Vallejo": {"CARDIO": 2, "ID": 2, "FLOORS": 11, "ICU": 4, "ED": 4, "NF": 8, "SWING": 2},
    "J. Perez": {"CARDIO": 1, "ID": 2, "FLOORS": 13, "ICU": 2, "ED": 0, "NF": 4, "SWING": 8},
    "C. Melguizo-Song": {"CARDIO": 1, "ID": 1, "FLOORS": 17, "ICU": 0, "ED": 0, "NF": 2, "SWING": 0},
    "C. Pantoja": {"CARDIO": 1, "ID": 3, "FLOORS": 8, "ICU": 6, "ED": 1, "NF": 8, "SWING": 0},
    "E. Mujica": {"CARDIO": 3, "ID": 2, "FLOORS": 10, "ICU": 3, "ED": 0, "NF": 2, "SWING": 1},
    "Y. Oliva": {"CARDIO": 1, "ID": 2, "FLOORS": 10, "ICU": 5, "ED": 0, "NF": 2, "SWING": 1},
    "A. Perez-Sanz": {"CARDIO": 0, "ID": 1, "FLOORS": 11, "ICU": 6, "ED": 0, "NF": 1, "SWING": 8},
    "D. Melendez": {"CARDIO": 2, "ID": 2, "FLOORS": 11, "ICU": 4, "ED": 0, "NF": 2, "SWING": 1},
    "M. Duarte": {"CARDIO": 1, "ID": 2, "FLOORS": 15, "ICU": 8, "ED": 0, "NF": 2, "SWING": 1},
    "H. Hussain": {"CARDIO": 2, "ID": 3, "FLOORS": 8, "ICU": 6, "ED": 0, "NF": 4, "SWING": 3},
    "M. De Mello": {"CARDIO": 3, "ID": 1, "FLOORS": 15, "ICU": 4, "ED": 0, "NF": 2, "SWING": 8},
}

# 1. Clear existing completions for these residents in year_id = 2
target_residents = db.query(Resident).filter(Resident.year_id == 2).all()
for r in target_residents:
    db.query(Completion).filter(Completion.resident_id == r.id).delete()

# 2. Apply the new numbers
for r in target_residents:
    if r.name in data:
        comps = data[r.name]
        for cat, weeks in comps.items():
            if weeks > 0:
                db.add(Completion(resident_id=r.id, category=cat, completed_weeks=weeks, source="image_sync"))

db.commit()
print("Base de datos actualizada con los totales de la imagen.")
db.close()
