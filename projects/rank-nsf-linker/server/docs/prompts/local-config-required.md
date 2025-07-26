# Local Config Required

```log
ERROR  [23:46:46] - main.go:42 failed to execute migrations: failed to execute migration 1_csv_file_schemas.sql: pq: pg_hba.conf rejects connection for host "142.250.187.27", user "myuser", database "mydb", no encryption
```

now that we have moved the postgres initiation to the docker-compose.yaml file,

```yaml
services:
  postgres:
    image: cgr.dev/chainguard/postgres
    container_name: pg17-local
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: strongpassword
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./conf/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro
      - ./conf/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: ["--config-file=/etc/postgresql/postgresql.conf"]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "myuser"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp

  go-server:
    container_name: go-server
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ../data:/app/data:rw
      - ./migrations:/app/migartions:ro
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: mydb
      DB_USER: myuser
      DB_PASSWORD: strongpassword
    ports:
      - "8080:8080"
    restart: unless-stopped
    command: ["./go-server"]

volumes:
  pg_data:
```

It causes an issue on the connection side during local.
