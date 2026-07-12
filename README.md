# CheckLectura

Web MVC para gestionar varios planes biblicos por usuario con acceso por nombre.

## Flujo

- Inicias sesion escribiendo solo tu nombre.
- Despues ves la lista de planes en los que participas.
- Cada plan tiene su propia pantalla con progreso, capitulos diarios, participantes, rachas y quien suele marcar antes.

## Estructura

- `backend/app/routes.py`: controladores y paginas HTML.
- `backend/app/services.py`: logica de planes, progreso y rachas.
- `backend/app/repository.py`: consultas a la BBDD.
- `backend/app/db.py`: esquema y semillas.
- `backend/app/templates/`: vistas HTML.
- `backend/app/static/`: estilos compartidos.

## Arranque

```bash
docker compose up --build
```

Despues:

- Web: `http://localhost:5667`
- Salud: `http://localhost:5667/health`

## Ngrok

```bash
ngrok http 5667
```

## DBeaver

Conecta a PostgreSQL con estos datos:

- Host: `localhost`
- Port: `5432`
- Database: `checklectura`
- User: `checklectura`
- Password: `checklectura`

## Paginas

- `/login`: acceso por nombre.
- `/plans`: lista de planes del usuario.
- `/plans/{id}`: detalle del plan.
