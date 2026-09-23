from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User, Domain, Subscription, TokenLog, Prompt
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv
import uuid
import os

# -------------------- USERS --------------------
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_handle(db: Session, handle: str):
    return db.query(User).filter(User.handle == handle).first()

def get_user_by_key(db: Session, key: str):
    return db.query(User).filter(User.api_key == key).first()

def create_user(db: Session, email: str, password_hash: str, handle: str, domain_name: str, superuser=False):
    # Create user
    new_user = User(
        email=email,
        password_hash=password_hash,
        handle=handle,
        superuser=superuser
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)

        # Create initial domain
        first_domain = Domain(
            user_id=new_user.id,
            domain_name=domain_name
        )
        db.add(first_domain)
        db.commit()
        db.refresh(first_domain)

        return new_user
    except IntegrityError:
        db.rollback()
        return None
    
def create_user_api_key(db: Session, user_id: int):
    """Create a new API key for a user with uniqueness guarantee"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if user.api_key == None:
    
        # Generate unique API key with collision checking
        max_attempts = 10  # Prevent infinite loops
        for attempt in range(max_attempts):
            new_api_key = str(uuid.uuid4())
            
            # Check if this key already exists in the database
            existing_user = db.query(User).filter(User.api_key == new_api_key).first()
            if not existing_user:
                # Key is unique, assign it
                user.api_key = new_api_key
                db.commit()
                db.refresh(user)
                return user.api_key
            
            raise Exception("Failed to generate unique API key after multiple attempts")
    
    else: return None
    
    # If we get here, we failed to generate a unique key after max_attempts

def delete_user_api_key(db: Session, user_id: int):
    """Delete/revoke the user's API key by setting it to None"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.api_key = None
    db.commit()
    db.refresh(user)
    return True



# ------------- models --------------
def set_model(db: Session, user_id: int, model_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.chosen_model = model_id   
        db.commit()                    
        db.refresh(user)               
        return user.chosen_model
    return None



# -------------------- DOMAINS --------------------
def add_domain(db: Session, user_id: int, domain_name: str):
    domain = Domain(user_id=user_id, domain_name=domain_name)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain

def get_domains_by_user(db: Session, user_id: int):
    return db.query(Domain).filter(Domain.user_id == user_id).all()

def delete_domain(db: Session, user_id: int, domain_name: str):
    # Find the domain belonging to this user
    domain = db.query(Domain).filter(
        Domain.user_id == user_id, 
        Domain.domain_name == domain_name
    ).first()
    
    if not domain:
        return False  # Domain not found or doesn't belong to user
    
    # Delete the domain
    db.delete(domain)
    db.commit()
    
    return True  # Successfully deleted
# -------------------- SUBSCRIPTIONS --------------------
def create_subscription(db: Session, user_id: int, tier: str, tokens_allocated: int, renewal_date: datetime):
    sub = Subscription(
        user_id=user_id,
        tier=tier,
        tokens_allocated=tokens_allocated,
        renewal_date=renewal_date
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

def get_subscription_by_user(db: Session, user_id: int):
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


#--- superuser


def update_user_superuser(db: Session, user_id: int, is_superuser: bool):
    user = get_user_by_id(db, user_id)
    if user:
        user.superuser = is_superuser
        db.commit()
        db.refresh(user)
    return user


def get_super_status_by_user(db: Session, user_id: int):
    return db.query(User.superuser).filter(User.id == user_id).first()[0]



# -------------------- TOKEN LOGS --------------------
def check_and_log_tokens(db, user, prompt_tokens, completion_tokens):
    now = datetime.now(timezone.utc)

    #Fetch the token log row with a lock  
    token_log = db.query(TokenLog).filter(TokenLog.user_id == user.id).with_for_update().first()

    #Monthly reset 
    if not user.last_refresh or user.last_refresh.month != now.month or user.last_refresh.year != now.year:
        if not token_log:
            token_log = TokenLog(
                user_id=user.id,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
            db.add(token_log)
        else:
            token_log.prompt_tokens = 0
            token_log.completion_tokens = 0
            token_log.total_tokens = 0

        user.last_refresh = now
        db.add(user)
        db.commit()
        db.refresh(user)

    # --- Token limit enforcement for non-superusers ---
    if not user.superuser:
        sub = get_subscription_by_user(db, user.id)
        tier = sub.tier if sub else "None"
        token_limits = {
            "Base": 100_000,
            "Plus": 500_000,
            "Premium": 2_000_000
        }.get(tier, 0)

        prev_tokens = token_log.total_tokens if token_log else 0
        if prev_tokens + prompt_tokens + completion_tokens > token_limits:
            return False, token_limits  # over limit

    # --- Update token log ---
    if not token_log:
        token_log = TokenLog(
            user_id=user.id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        db.add(token_log)
    else:
        token_log.prompt_tokens += prompt_tokens
        token_log.completion_tokens += completion_tokens
        token_log.total_tokens += prompt_tokens + completion_tokens

    db.commit()
    db.refresh(token_log)

    return True, token_log.total_tokens
def get_token_logs(db: Session, user_id: int):
    now = datetime.now(timezone.utc)
    return db.query(TokenLog).filter(TokenLog.user_id == user_id).first()



# -------------------- PROMPTS --------------------
def create_prompt(db: Session, user_id: int, custom_prompt: str, domain: str ):
    # Check if a prompt already exists for the user
    prompt = db.query(Prompt).filter(Prompt.user_id == user_id, Prompt.domain == domain).first()
    
    if prompt:
        # Update existing prompt
        prompt.custom_prompt = custom_prompt
    else:
        # Create new prompt
        prompt = Prompt(
            user_id=user_id,
            custom_prompt=custom_prompt,
            domain = domain
        )
        db.add(prompt)
    
    db.commit()
    db.refresh(prompt)
    return prompt

def save_prompt_data(db: Session, user_id: int, domain_name: str, language: str, FAQs: str, customer_service_info: str, app_name: str, scope: str):
    domain_obj = db.query(Domain).filter(Domain.domain_name == domain_name, Domain.user_id == user_id).first()
    
    if not domain_obj:
        raise ValueError(f"Domain '{domain_name}' not found for user {user_id}")

    domain_obj.language = language
    domain_obj.FAQs = FAQs
    domain_obj.customer_service_info = customer_service_info
    domain_obj.app_name = app_name
    domain_obj.scope = scope

    db.commit()
    db.refresh(domain_obj)
    return domain_obj

def get_prompt_by_user(db: Session, user_id: int, domain: str):
    return db.query(Prompt).filter(Prompt.user_id == user_id, Prompt.domain == domain).first()

#------ LOGIN -----
load_dotenv()
LOGIN_SESSION_KEY = os.environ.get("JWT_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password util ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# --- User auth / none = invalid email/password---
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# --- JWT helpers and tools ---
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, LOGIN_SESSION_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, LOGIN_SESSION_KEY, algorithms=[ALGORITHM])
        return payload  # contains user_id, email, etc.
    except JWTError:
        return None

def get_user_by_JWT(db: Session, jwt: str):
    try:
        payload = verify_access_token(jwt)
        user_id = int(payload["sub"])
        user = get_user_by_id(db, user_id)
        return user
    except Exception:
        return None