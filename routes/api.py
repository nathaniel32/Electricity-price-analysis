from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from pydantic import BaseModel
from database.connection import Connection
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends

db_connection = Connection(db_hostname="mssql")
db_connection.create_tables()

class SQLQuery(BaseModel):
    query: str

class DataAPI:
    def __init__(self):
        self.router = APIRouter(prefix="/api/control", tags=["Control"])
        self.router.add_api_route("/schema", self.schema, methods=["GET"])
        self.router.add_api_route("/query", self.query, methods=["POST"])

    async def schema(self):
        try:
            with open('database/schema.sql', 'r') as file:
                sql_script = file.read()
            return {"data": sql_script}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Schema file not found")

    def query(self, sql: SQLQuery, db: Annotated[Session, Depends(db_connection.get_db)]):
        query_text = sql.query
        if not query_text:
            raise HTTPException(status_code=400, detail="Missing 'query' in request body")

        try:
            result = db.execute(text(query_text))
            rows = result.fetchall()
            
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]

            return {"data": data}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))