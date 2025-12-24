"""
Database Manager Module - Supabase PostgreSQL

This module handles all Supabase database operations for the Confuser web app.
It stores conversation history to enable cross-user knowledge sharing.

Tables (in Supabase):
- profiles: User profiles linked to auth.users
- chat_sessions: Chat session metadata (id, user_id, title, created_at)
- chat_messages: Messages within sessions (session_id, role, content, peer_insights)
- conversations: Decoys for peer insights (source_id for deduplication)
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid
import json


def get_supabase_client() -> Client:
    """
    Get or create a Supabase client using Streamlit secrets.
    
    Returns:
        Client: Supabase client instance
    """
    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        st.session_state.supabase_client = create_client(url, key)
    
    return st.session_state.supabase_client


def get_current_user_id() -> str:
    """
    Get the current logged-in user's ID from session state.
    
    Returns:
        str: User ID or None if not logged in
    """
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.id
    return None


# ===================================================================
# PROFILE FUNCTIONS
# ===================================================================

def create_or_get_profile(user_id: str, email: str):
    """
    Create or fetch a user profile.
    Called after successful login/signup.
    
    Args:
        user_id (str): The auth.users UUID
        email (str): User's email
        
    Returns:
        dict: Profile data
    """
    try:
        supabase = get_supabase_client()
        
        # Try to get existing profile
        response = supabase.table('profiles').select('*').eq('id', user_id).execute()
        
        if response.data:
            return response.data[0]
        
        # Create new profile if doesn't exist
        profile_data = {
            'id': user_id,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('profiles').insert(profile_data).execute()
        return response.data[0] if response.data else None
        
    except Exception as e:
        print(f"❌ Error with profile: {e}")
        return None


# ===================================================================
# CHAT SESSION FUNCTIONS
# ===================================================================

def create_session(title: str = None) -> str:
    """
    Create a new chat session for the current user.
    
    Args:
        title (str): Optional title for the session
        
    Returns:
        str: The UUID of the created session, or None on failure
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            print("❌ No user logged in")
            return None
            
        supabase = get_supabase_client()
        
        session_id = str(uuid.uuid4())
        session_title = title if title else "New Chat"
        
        # Truncate title if too long
        if len(session_title) > 50:
            session_title = session_title[:47] + "..."
        
        session_data = {
            'id': session_id,
            'user_id': user_id,
            'title': session_title,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('chat_sessions').insert(session_data).execute()
        
        if response.data:
            return session_id
        return None
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None


def get_all_sessions(limit: int = 20) -> list:
    """
    Retrieve all chat sessions for the current user.
    
    Args:
        limit (int): Maximum number of sessions to return
        
    Returns:
        list: List of session dicts with id, title, created_at
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return []
            
        supabase = get_supabase_client()
        
        response = supabase.table('chat_sessions') \
            .select('id, title, created_at') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        # Convert to list of tuples for compatibility
        return [(s['id'], s['title'], s['created_at']) for s in response.data] if response.data else []
        
    except Exception as e:
        print(f"❌ Error retrieving sessions: {e}")
        return []


def get_messages_by_session(session_id: str) -> list:
    """
    Retrieve all messages for a specific chat session.
    
    Args:
        session_id (str): The UUID of the session
        
    Returns:
        list: List of message dicts with role, content, peer_insights
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return []
            
        supabase = get_supabase_client()
        
        # First verify the session belongs to this user
        session_check = supabase.table('chat_sessions') \
            .select('id') \
            .eq('id', session_id) \
            .eq('user_id', user_id) \
            .execute()
        
        if not session_check.data:
            print("❌ Session not found or doesn't belong to user")
            return []
        
        response = supabase.table('chat_messages') \
            .select('role, content, peer_insights') \
            .eq('session_id', session_id) \
            .order('timestamp', desc=False) \
            .execute()
        
        messages = []
        for row in response.data or []:
            msg = {
                "role": row['role'],
                "content": row['content']
            }
            # Parse peer_insights JSON if present
            if row.get('peer_insights'):
                try:
                    msg["peer_insights"] = json.loads(row['peer_insights']) if isinstance(row['peer_insights'], str) else row['peer_insights']
                except:
                    msg["peer_insights"] = []
            messages.append(msg)
        
        return messages
        
    except Exception as e:
        print(f"❌ Error retrieving messages: {e}")
        return []


def save_message(session_id: str, role: str, content: str, peer_insights: list = None) -> str:
    """
    Save a message to a chat session.
    
    Args:
        session_id (str): The UUID of the session
        role (str): "user" or "assistant"
        content (str): The message content
        peer_insights (list): Optional list of peer insight dicts
        
    Returns:
        str: The ID of the inserted message, or None on failure
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            print("❌ No user logged in")
            return None
            
        supabase = get_supabase_client()
        
        message_data = {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'user_id': user_id,
            'role': role,
            'content': content,
            'peer_insights': json.dumps(peer_insights) if peer_insights else None,
            'timestamp': datetime.now().isoformat()
        }
        
        response = supabase.table('chat_messages').insert(message_data).execute()
        
        return response.data[0]['id'] if response.data else None
        
    except Exception as e:
        print(f"❌ Error saving message: {e}")
        return None


def update_session_title(session_id: str, new_title: str):
    """
    Update the title of an existing session.
    
    Args:
        session_id (str): The UUID of the session
        new_title (str): The new title
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return
            
        # Truncate title if too long
        if len(new_title) > 50:
            new_title = new_title[:47] + "..."
            
        supabase = get_supabase_client()
        
        supabase.table('chat_sessions') \
            .update({'title': new_title}) \
            .eq('id', session_id) \
            .eq('user_id', user_id) \
            .execute()
        
    except Exception as e:
        print(f"❌ Error updating session title: {e}")


def delete_session(session_id: str):
    """
    Delete a chat session and all its messages.
    
    Args:
        session_id (str): The UUID of the session to delete
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return
            
        supabase = get_supabase_client()
        
        # Delete messages first
        supabase.table('chat_messages') \
            .delete() \
            .eq('session_id', session_id) \
            .execute()
        
        # Delete session (with user_id check for security)
        supabase.table('chat_sessions') \
            .delete() \
            .eq('id', session_id) \
            .eq('user_id', user_id) \
            .execute()
        
        print(f"✅ Session {session_id[:8]}... deleted")
        
    except Exception as e:
        print(f"❌ Error deleting session: {e}")


# ===================================================================
# CONVERSATION/DECOY FUNCTIONS (For Peer Insights)
# ===================================================================

def save_conversation(query: str, response: str, is_decoy: bool = False, parent_id: str = None, source_id: str = None) -> str:
    """
    Save a conversation (decoy) to the database.
    
    Args:
        query (str): The conversation query
        response (str): The AI's response
        is_decoy (bool): Whether this is a generated decoy
        parent_id (str): ID of the original conversation (if decoy)
        source_id (str): Batch ID to group sibling decoys
        
    Returns:
        str: The ID of the inserted row, or None on failure
    """
    try:
        supabase = get_supabase_client()
        
        conv_data = {
            'id': str(uuid.uuid4()),
            'original_query': query,
            'ai_response': response,
            'is_decoy': is_decoy,
            'parent_id': parent_id,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat()
        }
        
        response_obj = supabase.table('conversations').insert(conv_data).execute()
        
        return response_obj.data[0]['id'] if response_obj.data else None
        
    except Exception as e:
        print(f"❌ Error saving conversation: {e}")
        return None


def get_all_queries() -> list:
    """
    Retrieve queries from the database for Semantic Matching (Layer 1).
    
    PRIVACY: This fetches ONLY DECOYS.
    
    Returns:
        list: List of tuples (id, query_text, timestamp, source_id)
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('conversations') \
            .select('id, original_query, timestamp, source_id') \
            .eq('is_decoy', True) \
            .order('timestamp', desc=True) \
            .execute()
        
        # Convert to list of tuples for compatibility
        return [(c['id'], c['original_query'], c['timestamp'], c['source_id']) for c in response.data] if response.data else []
        
    except Exception as e:
        print(f"❌ Error retrieving queries: {e}")
        return []


def get_response_by_query(query_text: str) -> str:
    """
    Retrieve the AI response for a specific query.
    
    Args:
        query_text (str): The query to search for
        
    Returns:
        str: The AI response or None
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('conversations') \
            .select('ai_response') \
            .eq('original_query', query_text) \
            .limit(1) \
            .execute()
        
        return response.data[0]['ai_response'] if response.data else None
        
    except Exception as e:
        print(f"❌ Error retrieving response: {e}")
        return None


def get_conversation_count() -> int:
    """
    Get the total number of conversations (decoys).
    
    Returns:
        int: Count of conversations
    """
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('conversations') \
            .select('id', count='exact') \
            .execute()
        
        return response.count if response.count else 0
        
    except Exception as e:
        print(f"❌ Error counting conversations: {e}")
        return 0


def clear_all_conversations():
    """
    Clear all conversations from the database.
    
    WARNING: This deletes all decoy data permanently!
    """
    try:
        supabase = get_supabase_client()
        
        # Delete all conversations
        supabase.table('conversations').delete().neq('id', '').execute()
        
        print("✅ All conversations cleared")
        
    except Exception as e:
        print(f"❌ Error clearing conversations: {e}")


# ===================================================================
# INITIALIZATION (No-op for Supabase - tables created via Dashboard)
# ===================================================================

def init_db():
    """
    Initialize database connection.
    For Supabase, tables should be created via the Dashboard or SQL Editor.
    This function just validates the connection.
    """
    try:
        supabase = get_supabase_client()
        # Quick health check
        print("✅ Supabase connection initialized")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        raise


# Print SQL for table creation (to be run in Supabase SQL Editor)
SUPABASE_SCHEMA_SQL = """
-- Run this in Supabase SQL Editor to create required tables

-- 1. Profiles table (linked to auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- 2. Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own sessions
CREATE POLICY "Users can view own sessions" ON chat_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON chat_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON chat_sessions
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON chat_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- 3. Chat Messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    peer_insights JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their own messages
CREATE POLICY "Users can view own messages" ON chat_messages
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own messages" ON chat_messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own messages" ON chat_messages
    FOR DELETE USING (auth.uid() = user_id);

-- 4. Conversations table (for decoys - PUBLIC for peer insights)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_query TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    is_decoy BOOLEAN DEFAULT FALSE,
    parent_id UUID,
    source_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS but allow public read for decoys
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Anyone can read decoys (they're anonymized)
CREATE POLICY "Anyone can read decoys" ON conversations
    FOR SELECT USING (is_decoy = TRUE);

-- RLS Policy: Service role can insert (from backend)
CREATE POLICY "Service can insert conversations" ON conversations
    FOR INSERT WITH CHECK (TRUE);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_source_id ON conversations(source_id);
CREATE INDEX IF NOT EXISTS idx_conversations_is_decoy ON conversations(is_decoy);
"""

if __name__ == "__main__":
    print("\n=== Supabase Schema SQL ===\n")
    print("Copy and paste this into your Supabase SQL Editor:\n")
    print(SUPABASE_SCHEMA_SQL)
