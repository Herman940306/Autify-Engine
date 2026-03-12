from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # "admin" or "user"
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)


class Client(Base):
    __tablename__ = 'clients'

    client_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    company = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)
    last_update = Column(DateTime)

class Input(Base):
    __tablename__ = 'inputs'
    
    input_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'))
    file_name = Column(String)
    file_type = Column(String)
    parsed_data = Column(JSON)
    upload_time = Column(DateTime)

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    
    result_id = Column(Integer, primary_key=True, index=True)
    input_id = Column(Integer, ForeignKey('inputs.input_id'))
    kpi_summary = Column(JSON)
    anomalies = Column(JSON)
    timestamp = Column(DateTime)

class DraftOutput(Base):
    __tablename__ = 'draft_outputs'
    
    draft_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey('analysis_results.result_id'))
    draft_type = Column(String)  # e.g., 'email', 'calendar', 'report'
    content = Column(JSON)       # the AI generated draft
    approved = Column(Boolean, default=False)
    approval_time = Column(DateTime, nullable=True)
    rejected = Column(Boolean, default=False)
    rejected_at = Column(DateTime, nullable=True)

class Log(Base):
    __tablename__ = 'logs'
    
    log_id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey('draft_outputs.draft_id'), nullable=True)
    action = Column(String)      # action taken, e.g., 'approve', 'reject', 'upload'
    timestamp = Column(DateTime)
    user_id = Column(String)     # user doing the action


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    message_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime)
    session_id = Column(String, nullable=True)
