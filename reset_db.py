import database
database.FailedPayment.__table__.drop(database.engine, checkfirst=True)
database.RecoveryAuditLog.__table__.drop(database.engine, checkfirst=True)
database.Base.metadata.create_all(database.engine)
print("Database reset with new schema!")
