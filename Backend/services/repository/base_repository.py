"""
Base Repository Pattern for Standardized Database Access
Addresses standardization of database access patterns across services
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from contextlib import contextmanager

from database.unified_database_manager import UnifiedDatabaseManager as DatabaseManager

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository for standardized database operations
    Provides common CRUD operations and transaction management
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the primary table name for this repository"""
        pass
    
    @abstractmethod
    def _row_to_model(self, row: Dict[str, Any]) -> T:
        """Convert database row to domain model"""
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert domain model to dictionary for database insertion/update"""
        pass
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        try:
            with self.db_manager.get_connection() as conn:
                yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise
    
    @contextmanager
    def transaction(self):
        """Execute operations within a transaction"""
        try:
            if hasattr(self.db_manager, 'transaction'):
                with self.db_manager.transaction() as conn:
                    yield conn
            else:
                # Fallback for basic connection
                with self.get_connection() as conn:
                    try:
                        yield conn
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        raise
        except Exception as e:
            self.logger.error(f"Transaction error: {e}")
            raise
    
    def find_by_id(self, id_value: Union[int, str]) -> Optional[T]:
        """Find entity by primary key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id_value,))
                row = cursor.fetchone()
                
                if row:
                    if hasattr(row, '_asdict'):
                        return self._row_to_model(row._asdict())
                    elif isinstance(row, dict):
                        return self._row_to_model(row)
                    else:
                        # Convert sqlite3.Row to dict
                        return self._row_to_model(dict(row))
                return None
        except Exception as e:
            self.logger.error(f"Error finding {self.table_name} by id {id_value}: {e}")
            raise
    
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Find all entities with optional pagination"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {self.table_name}"
                params = []
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                    
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    if hasattr(row, '_asdict'):
                        results.append(self._row_to_model(row._asdict()))
                    elif isinstance(row, dict):
                        results.append(self._row_to_model(row))
                    else:
                        results.append(self._row_to_model(dict(row)))
                
                return results
        except Exception as e:
            self.logger.error(f"Error finding all {self.table_name}: {e}")
            raise
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities by custom criteria"""
        try:
            if not criteria:
                return self.find_all()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause
                conditions = []
                params = []
                for key, value in criteria.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                
                query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join(conditions)}"
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    if hasattr(row, '_asdict'):
                        results.append(self._row_to_model(row._asdict()))
                    elif isinstance(row, dict):
                        results.append(self._row_to_model(row))
                    else:
                        results.append(self._row_to_model(dict(row)))
                
                return results
        except Exception as e:
            self.logger.error(f"Error finding {self.table_name} by criteria {criteria}: {e}")
            raise
    
    def save(self, entity: T) -> T:
        """Save entity (insert or update)"""
        try:
            data = self._model_to_dict(entity)
            
            with self.transaction() as conn:
                cursor = conn.cursor()
                
                # Check if entity has an ID (update vs insert)
                if 'id' in data and data['id'] is not None:
                    return self._update(cursor, entity, data)
                else:
                    return self._insert(cursor, entity, data)
        except Exception as e:
            self.logger.error(f"Error saving {self.table_name}: {e}")
            raise
    
    def delete_by_id(self, id_value: Union[int, str]) -> bool:
        """Delete entity by primary key"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id_value,))
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting {self.table_name} with id {id_value}: {e}")
            raise
    
    def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if criteria:
                    conditions = []
                    params = []
                    for key, value in criteria.items():
                        conditions.append(f"{key} = ?")
                        params.append(value)
                    
                    query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {' AND '.join(conditions)}"
                    cursor.execute(query, params)
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error counting {self.table_name}: {e}")
            raise
    
    def _insert(self, cursor, entity: T, data: Dict[str, Any]) -> T:
        """Internal method for inserting new entity"""
        # Remove id from data for insert
        insert_data = {k: v for k, v in data.items() if k != 'id'}
        
        columns = list(insert_data.keys())
        placeholders = ['?'] * len(columns)
        values = list(insert_data.values())
        
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        
        # Update entity with new ID
        new_id = cursor.lastrowid
        if hasattr(entity, 'id'):
            entity.id = new_id
        
        return entity
    
    def _update(self, cursor, entity: T, data: Dict[str, Any]) -> T:
        """Internal method for updating existing entity"""
        entity_id = data.pop('id')
        
        if not data:
            return entity
        
        set_clauses = [f"{key} = ?" for key in data.keys()]
        values = list(data.values()) + [entity_id]
        
        query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, values)
        
        return entity
    
    def execute_raw_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute raw SQL query - use sparingly and with caution"""
        self.logger.warning(f"Executing raw query: {query}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    if hasattr(row, '_asdict'):
                        results.append(row._asdict())
                    elif isinstance(row, dict):
                        results.append(row)
                    else:
                        results.append(dict(row))
                
                return results
        except Exception as e:
            self.logger.error(f"Error executing raw query: {e}")
            raise
