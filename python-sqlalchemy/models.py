from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, create_engine
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()

# --- Users ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=True, unique=True)  
    api_key = Column(String, unique=True, nullable=True, default=lambda: str(uuid.uuid4()))
    handle = Column(String, unique=True, nullable=False)
    superuser = Column(Boolean, nullable=False, default=False)
    chosen_model = Column(Integer, default= 0, nullable=True)   # 0 - gemma 3 27B, 1 - deepseek v3, 2 - gpt oss, 3 - glm 4.5, 4 - kimi k2, 5 - dolphin mistrall
    created_at = Column(DateTime, default=datetime.utcnow)
    last_refresh = Column(DateTime, default=datetime.utcnow)

    domains = relationship("Domain", back_populates="user",cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    token_logs = relationship("TokenLog", back_populates="user", cascade="all, delete-orphan")
    prompt = relationship("Prompt", uselist=False, back_populates="user" , cascade="all, delete-orphan")


# --- Subscriptions ---
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tier = Column(String, nullable=False)  # "Base", "Plus", "Premium"
    renewal_date = Column(DateTime, nullable=False)
    starting_date= Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscription")


# --- Token usage logs ---
class TokenLog(Base):
    __tablename__ = "token_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="token_logs")

# --- domains ---
class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain_name = Column(String, unique=True, nullable=False)  # each domain is unique
    language = Column(String, nullable=True)
    FAQs = Column(Text, nullable=True)
    app_name = Column(String, nullable= True)
    scope = Column(Text, nullable=True)
    customer_service_info = Column(Text, nullable=True)

    user = relationship("User", back_populates="domains")



# --- Prompt (custom instructions + FAQs) ---
class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    custom_prompt = Column(Text, nullable=False)  # long text for FAQs, instructions
    domain = Column(String, nullable=True)  # associated domain
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="prompt")


