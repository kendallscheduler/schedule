
from database import SessionLocal
from models import Resident, Completion

db = SessionLocal()

data = {
    "PGY1": [
        ("B. Perez", [2, 2, 2, 0, 0]),
        ("L. Duarte", [3, 0, 2, 0, 0]),
        ("J. Jhooty", [3, 2, 2, 0, 0]),
        ("M. Artavia", [2, 1, 2, 0, 0]),
        ("M. Delgadillo", [2, 2, 2, 0, 0]),
        ("K. Gonzalez", [4, 2, 2, 0, 0]),
        ("M. Cruz", [5, 2, 0, 0, 0]),
        ("I. Estrada", [0, 2, 2, 0, 0]),
        ("M. Rivas", [2, 2, 2, 0, 0]),
        ("R. Bernal", [3, 4, 2, 0, 0]),
        ("A. Gonzalez", [4, 1, 2, 0, 0]),
        ("N. Monroig", [2, 1, 2, 0, 0]),
        ("C. Tucci", [2, 2, 2, 0, 0]),
        ("L. Cordoba", [2, 3, 2, 0, 0]),
    ],
    "PGY2": [
        ("M. Garcia", [4, 5, 4, 2, 0]),
        ("D. Cano", [4, 6, 4, 2, 0]),
        ("C. Ayala", [4, 4, 4, 2, 0]),
        ("K. Vallejo", [2, 2, 4, 4, 0]),
        ("J. Cabrera", [3, 2, 4, 3, 0]),
        ("J. Perez", [3, 2, 4, 4, 0]),
        ("E. Mujica", [3, 3, 4, 3, 0]),
        ("Y. Oliva", [4, 4, 4, 1, 0]),
        ("A. Perez-Sanz", [3, 2, 4, 1, 0]),
        ("O. Melendez", [4, 3, 4, 4, 0]),
        ("M. Osorio", [3, 2, 4, 2, 0]),
        ("H. Hussain", [3, 4, 4, 4, 0]),
        ("M. De Mello", [4, 3, 4, 4, 0]),
        ("A. Pueyo", [4, 6, 4, 4, 0]),
    ]
}

categories = ["CARDIO", "ID", "ED", "NEURO", "GERIATRICS"]

for pgy, residents_list in data.items():
    for name, counts in residents_list:
        # Find resident by name and pgy
        res = db.query(Resident).filter(Resident.name == name, Resident.pgy == pgy).first()
        if not res:
            print(f"Warning: Resident {name} ({pgy}) not found in DB.")
            continue
        
        for i, count in enumerate(counts):
            cat = categories[i]
            # Upsert completion
            comp = db.query(Completion).filter(Completion.resident_id == res.id, Completion.category == cat).first()
            if comp:
                comp.completed_weeks = count
            else:
                db.add(Completion(resident_id=res.id, category=cat, completed_weeks=count, source="manual"))

db.commit()
print("Completions successfully updated.")
db.close()
