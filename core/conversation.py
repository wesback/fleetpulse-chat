"""Conversation history management for FleetPulse chatbot."""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from core.genai_manager import ChatMessage
from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Conversation data structure."""
    id: Optional[int] = None
    title: str = "New Conversation"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    provider: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationMessage:
    """Individual message in a conversation."""
    id: Optional[int] = None
    conversation_id: int = 0
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationManager:
    """Manages conversation history and persistence."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.settings = get_settings()
        self.db_path = db_path or "fleetpulse_conversations.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database and tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL DEFAULT 'New Conversation',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        provider TEXT,
                        system_prompt TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                    ON messages(conversation_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
                    ON conversations(updated_at DESC)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_conversation(
        self, 
        title: str = "New Conversation",
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO conversations (title, provider, system_prompt, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    title,
                    provider,
                    system_prompt,
                    json.dumps(metadata) if metadata else None
                ))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                
                return Conversation(
                    id=conversation_id,
                    title=title,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    provider=provider,
                    system_prompt=system_prompt,
                    metadata=metadata
                )
        
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, created_at, updated_at, provider, system_prompt, metadata
                    FROM conversations WHERE id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if row:
                    return Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        provider=row[4],
                        system_prompt=row[5],
                        metadata=json.loads(row[6]) if row[6] else None
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 50) -> List[Conversation]:
        """List recent conversations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, created_at, updated_at, provider, system_prompt, metadata
                    FROM conversations 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                """, (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append(Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        provider=row[4],
                        system_prompt=row[5],
                        metadata=json.loads(row[6]) if row[6] else None
                    ))
                
                return conversations
        
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def update_conversation(
        self, 
        conversation_id: int, 
        title: Optional[str] = None,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update conversation metadata."""
        try:
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if provider is not None:
                updates.append("provider = ?")
                params.append(provider)
            
            if system_prompt is not None:
                updates.append("system_prompt = ?")
                params.append(system_prompt)
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            if not updates:
                return True  # Nothing to update
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(conversation_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    UPDATE conversations 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
                return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            return False
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete messages first
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                
                # Delete conversation
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def add_message(
        self, 
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    conversation_id,
                    role,
                    content,
                    json.dumps(metadata) if metadata else None
                ))
                
                message_id = cursor.lastrowid
                
                # Update conversation timestamp
                cursor.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                
                return ConversationMessage(
                    id=message_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    timestamp=datetime.now(),
                    metadata=metadata
                )
        
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            raise
    
    def get_messages(self, conversation_id: int) -> List[ConversationMessage]:
        """Get all messages for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, conversation_id, role, content, timestamp, metadata
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append(ConversationMessage(
                        id=row[0],
                        conversation_id=row[1],
                        role=row[2],
                        content=row[3],
                        timestamp=datetime.fromisoformat(row[4]) if row[4] else None,
                        metadata=json.loads(row[5]) if row[5] else None
                    ))
                
                return messages
        
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    def get_chat_history(self, conversation_id: int) -> List[ChatMessage]:
        """Get messages formatted for AI chat completion."""
        messages = self.get_messages(conversation_id)
        
        chat_messages = []
        for msg in messages:
            chat_messages.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp.isoformat() if msg.timestamp else None
            ))
        
        return chat_messages
    
    def clear_messages(self, conversation_id: int) -> bool:
        """Clear all messages from a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                
                # Update conversation timestamp
                cursor.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                return True
        
        except Exception as e:
            logger.error(f"Failed to clear messages for conversation {conversation_id}: {e}")
            return False
    
    def export_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Export a conversation with all messages."""
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            messages = self.get_messages(conversation_id)
            
            return {
                "conversation": asdict(conversation),
                "messages": [asdict(msg) for msg in messages],
                "exported_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to export conversation {conversation_id}: {e}")
            return None
    
    def search_conversations(self, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by title or content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at, 
                           c.provider, c.system_prompt, c.metadata
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.title LIKE ? OR m.content LIKE ?
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append(Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        provider=row[4],
                        system_prompt=row[5],
                        metadata=json.loads(row[6]) if row[6] else None
                    ))
                
                return conversations
        
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []