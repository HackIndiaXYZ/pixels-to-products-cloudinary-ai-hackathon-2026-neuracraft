"""
Create a demo user for easy testing
"""
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def create_demo_user():
    db = SessionLocal()
    try:
        # Check if demo user exists
        demo_email = "demo@creativepulse.ai"
        existing = db.query(User).filter(User.email == demo_email).first()
        
        if existing:
            print(f"✓ Demo user already exists: {demo_email}")
            print(f"  Password: demo123")
            return
        
        # Create demo user
        demo_user = User(
            email=demo_email,
            password_hash=hash_password("demo123")
        )
        db.add(demo_user)
        db.commit()
        
        print(f"✓ Demo user created successfully!")
        print(f"  Email: {demo_email}")
        print(f"  Password: demo123")
        print(f"\nYou can now login at http://localhost:3000/login")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_user()
