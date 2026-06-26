from backend.app.database import SessionLocal, Base, engine
from backend.app.services.seed import seed_builtin_packs, seed_tool_definitions

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    seed_tool_definitions(db)
    seed_builtin_packs(db)
    print("Seeded tools and template packs.")
finally:
    db.close()
