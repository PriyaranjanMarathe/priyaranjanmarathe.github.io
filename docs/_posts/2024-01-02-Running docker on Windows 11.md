---
layout: "default"
title: "Running docker on Windows 11"
comments: true
date: "2024-01-02"
categories: tils
---

# Running Docker on Windows 11
**Learning Notes**  
_Please don’t scream and ask, WHY. One has to do what one has to do. Or, as Haruki Murakami says, “I can bear any pain as long as it has meaning.“_

---

## The Ask
Running Docker on Windows 11 without Docker Desktop, WSL, or Docker Engine (since it’s not free on Windows Server versions). And if you feel particularly ambitious, let’s also make it work across other Windows and Linux flavors.

The challenge is clear: how do you install and run Docker containers natively on a Windows environment without falling back on typical tools like Docker Desktop or the Windows Subsystem for Linux (WSL)?

---

## Step 1: Setting the Scene with PowerShell
PowerShell is clutch here. Let’s walk through the Docker installation process using Microsoft’s container support and PowerShell commands.

```bash
docker --version

If Docker is installed, this will give you a version output. If not, it’s time to get your hands dirty.

Step 2: Installing Docker
You can follow Microsoft’s guide to get Docker set up without Docker Desktop. Here’s the key part of the script for installing Docker on Windows, including enabling Hyper-V and containers:

powershell
Copy
Edit
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All
Enable-WindowsOptionalFeature -Online -FeatureName Containers -All
Restart your system to apply the changes. Then:

bash
Copy
Edit
Install-Package -Name docker -ProviderName DockerMsftProvider
Once installed, check if the daemon is running:

bash
Copy
Edit
docker ps
At this point, Docker is running on Windows 11 without Docker Desktop or WSL.

Step 3: Building Docker Containers on Windows Server
Windows containers need specific base images. For example:

dockerfile
Copy
Edit
# Use the Windows Server Core base image
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Set the working directory
WORKDIR /app

# Download Python installer
ADD https://www.python.org/ftp/python/3.10.8/python-3.10.8-amd64.exe .

# Install Python silently
RUN python-3.10.8-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Clean up
RUN del python-3.10.8-amd64.exe

# Run Python script
CMD ["python", "your_script.py"]
Step 4: Troubleshooting Common Issues
SSL Certificate Errors
Use pip’s trusted-host config:

bash
Copy
Edit
pip config set global.trusted-host pypi.org files.pythonhosted.org pypi.python.org
Unsupported Daemon Requests
If you see errors like hcs::CreateComputeSystem, confirm that Hyper-V is properly enabled.

Step 5: Integrating SQLite with Your FastAPI App
SQLite is lightweight and includes the sqlite3 module in Python’s standard library.

Dockerfile Example
dockerfile
Copy
Edit
# Use the Windows Server Core base image
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Set the working directory
WORKDIR /app

# Download Python installer
ADD https://www.python.org/ftp/python/3.10.8/python-3.10.8-amd64.exe .

# Install Python silently
RUN python-3.10.8-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Remove the installer
RUN del python-3.10.8-amd64.exe

# Set pip trusted hosts (important for avoiding SSL errors)
RUN pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org" --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app/ ./app/

# Copy the database folder into the container
COPY db/ ./db/

# Expose port 8000
EXPOSE 8000

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "app.search_api:app", "--host", "0.0.0.0", "--port", "8000"]
FastAPI Code with SQLite Integration
python
Copy
Edit
import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, model_validator

app = FastAPI()

# Database configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
database_directory = os.path.join(BASE_DIR, '../db')

if not os.path.exists(database_directory):
    os.makedirs(database_directory)

database_name = 'sample_database.db'
database_path = os.path.join(database_directory, database_name)
table_name = 'sample_table'

# Initialize SQLite database
def initialize_database():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if not cursor.fetchone():
        cursor.execute(f'''
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            email TEXT
        )
        ''')
        conn.commit()
        print(f"Table '{table_name}' created.")
    conn.close()

# Fetch allowed columns from SQLite database
def get_allowed_columns():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    columns_info = cursor.fetchall()
    conn.close()
    return [column[1] for column in columns_info]

@app.on_event("startup")
def startup_event():
    initialize_database()
    global allowed_columns
    allowed_columns = get_allowed_columns()

class Record(BaseModel):
    data: Dict[str, Any]

    @model_validator(mode='after')
    def validate_columns(cls, values):
        data = values.data
        invalid_columns = [col for col in data.keys() if col not in allowed_columns]
        if invalid_columns:
            raise ValueError(f"Invalid columns: {', '.join(invalid_columns)}")
        return values

@app.post("/records", response_model=Record)
def create_record(record: Record):
    data = record.data
    columns = ', '.join(f'"{col}"' for col in data.keys())
    placeholders = ', '.join('?' for _ in data)
    values = tuple(data.values())

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
    try:
        cursor.execute(query, values)
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    conn.close()

    return record

@app.get("/records", response_model=List[Record])
def read_records(
    column: Optional[str] = Query(None, description="The column name to filter"),
    value: Optional[str] = Query(None, description="The value to filter by")
):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    if column and value:
        if column not in allowed_columns:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid column name.")
        query = f'SELECT * FROM "{table_name}" WHERE "{column}" = ?'
        cursor.execute(query, (value,))
    else:
        query = f'SELECT * FROM "{table_name}"'
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No records found.")

    column_names = allowed_columns
    results = []
    for row in rows:
        row_dict = dict(zip(column_names, row))
        results.append(Record(data=row_dict))

    return results

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.get("/tables")
def list_tables():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        return {"message": "No tables found"}

    table_details = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        table_details[table_name] = [{"name": col[1], "type": col[2]} for col in columns]

    conn.close()
    return table_details
Testing SQLite with Docker
Example cURL commands:

Create a record

bash
Copy
Edit
curl -X POST "http://localhost:8000/records" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"data": {"name": "John", "age": 30, "email": "john@example.com"}}'
Read all records

bash
Copy
Edit
curl -X GET "http://localhost:8000/records" \
     -H "accept: application/json"
List tables

bash
Copy
Edit
curl -X GET "http://localhost:8000/tables" \
     -H "accept: application/json"
Wrapping Up
By rolling with SQLite, you’ve got a compact setup that’s easy to manage in Docker. This method outlines building, running, and testing an app on Windows 11 without Docker Desktop or WSL—no screaming needed.

