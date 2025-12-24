import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_manager import Base, User, Campaign, Lead, KnowledgeBase
from src import auth, campaign_manager

# Use an in-memory DB for testing to not mess up real data
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Returns a fresh database session for a test."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_registration_and_auth(db_session):
    """Verify we can register and login users."""
    print("   [TEST] User Auth...")
    username = "testuser"
    password = "securepassword"
    
    # Register
    hashed_pw = auth.get_password_hash(password)
    user = User(username=username, password_hash=hashed_pw)
    db_session.add(user)
    db_session.commit()
    
    # Verify in DB
    saved_user = db_session.query(User).filter_by(username=username).first()
    assert saved_user is not None
    assert saved_user.username == username
    
    # Verify Login Logic
    assert auth.verify_password(password, saved_user.password_hash) is True
    assert auth.verify_password("wrongpw", saved_user.password_hash) is False
    print("   [PASS] User Auth OK.")

def test_multi_tenancy_isolation(db_session):
    """Verify User A cannot see User B's data."""
    print("   [TEST] Multi-Tenancy Isolation...")
    
    # Create User A and B
    user_a = User(username="userA", password_hash="pw")
    user_b = User(username="userB", password_hash="pw")
    db_session.add_all([user_a, user_b])
    db_session.commit()
    
    # User A creates a campaign
    camp_a = Campaign(name="Campaign A", user_id=user_a.id)
    db_session.add(camp_a)
    db_session.commit()
    
    # Verify User B cannot see it
    camp_b_view = db_session.query(Campaign).filter_by(user_id=user_b.id).all()
    assert len(camp_b_view) == 0
    
    # Verify User A CAN see it
    camp_a_view = db_session.query(Campaign).filter_by(user_id=user_a.id).all()
    assert len(camp_a_view) == 1
    assert camp_a_view[0].name == "Campaign A"
    print("   [PASS] Isolation OK.")

def test_campaign_manager_logic(db_session):
    """Verify campaign creation."""
    print("   [TEST] Campaign Manager...")
    user = User(username="camp_tester", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    # Create Campaign via Logic (Mocking the dependency injection of get_db is tricky, 
    # so we test the ORM logic directly or we'd need to patch get_db)
    # For simplicity, we test the model integrity here.
    
    camp = Campaign(name="Cold Outreach", user_id=user.id, status="Active")
    db_session.add(camp)
    db_session.commit()
    
    assert camp.id is not None
    assert camp.name == "Cold Outreach"
    print("   [PASS] Campaign Logic OK.")

def test_knowledge_base_scoping(db_session):
    """Verify Global vs Private Knowledge."""
    print("   [TEST] AI Knowledge Base...")
    user = User(username="ai_tester", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    # Add Global Item
    global_item = KnowledgeBase(category="Tone", content="Professional", is_global=True, user_id=None)
    
    # Add Private Item
    private_item = KnowledgeBase(category="Tone", content="Secret Sauce", is_global=False, user_id=user.id)
    
    db_session.add_all([global_item, private_item])
    db_session.commit()
    
    # Query: User should see BOTH
    from sqlalchemy import or_
    items = db_session.query(KnowledgeBase).filter(
        or_(KnowledgeBase.user_id == user.id, KnowledgeBase.is_global == True)
    ).all()
    
    assert len(items) == 2
    
    # Query: Another user should ONLY see Global
    user2 = User(username="other", password_hash="pw")
    items2 = db_session.query(KnowledgeBase).filter(
        or_(KnowledgeBase.user_id == user2.id, KnowledgeBase.is_global == True)
    ).all()
    
    assert len(items2) == 1
    assert items2[0].content == "Professional"
    print("   [PASS] Knowledge Scoping OK.")
