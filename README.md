# Medbot: Pulse Rate and Blood Pressure Monitor

The Medbot functionalities
- Measure pulse rate, blood pressure and blood saturation
- Print results in thermal paper
- Voice commands and voice prompts
- Arm and finger placement detection
- Sanitize

## Run
To use the Medbot class, we first need to create a Database class instance to store users and readings information
### Database
To create an instance of database class, pass in the `host,database,user,password` as args
```python
from database import Database
database = Database(host,database,user,password)
```
The database class uses python MySQL connector
#### Users table
| id | name | birthday | gender | phone_number | address | email | bio | profile_picture_path | email_verified_at | password | type | remember_token | created_at | updated_at |
|----|------|----------|--------|--------------|---------|-------|-----|----------------------|-------------------|----------|------|----------------|------------|------------|
|unique-auto increment| string | datetime | string | string | string | string-unique | string | string | string | hash | string | string | datetime | datetime |

To initialze the Medbot class, simply
