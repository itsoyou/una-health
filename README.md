# una-health coding challenge

### 1. Build and start services
docker-compose up --build

### 2. Access FastAPI at:
http://localhost:8000/docs

### Limitations

1. data schema is limited to 
 - user_id = Column(UUID(as_uuid=True), nullable=False)
 - device = Column(String, nullable=True)
 - serial_number = Column(String, nullable=True)
 - device_timestamp = Column(DateTime, nullable=True)
 - record_type = Column(Integer, nullable=True)
 - glucose_value = Column(Integer, nullable=True)
 - glucose_scan = Column(Integer, nullable=True)

2. No sorting options from /api/v1/levels/

3. Export feature, e.g. to JSON , CSV , or Excel in the API is not ready yet.

4. Solution is not available online.

5. Versioning, Linting, and Test Codes

### Covered

1. /api/v1/levels/ : Retrieves a list of glucose levels for a given
user_id , filter by start and stop timestamps. This endpoint
supports pagination, and a way to limit the number of
glucose levels returned.

2. /api/v1/levels/<id>/ : Retrieves a particular glucose level by record id.

3. POST endpoint to fill / pre-populate the model / database via an
API endpoint.

4. Create means to run the solution locally via Docker Compose.
