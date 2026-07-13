# CheckLectura — guía para desarrolladores

Documentación técnica para ejecutar y mantener CheckLectura en local.

## Stack

- Backend: FastAPI con plantillas Jinja.
- Base de datos: PostgreSQL 16.
- Estilos: CSS propio, sin framework.
- Entorno local: Docker Compose.

## Arranque

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Una vez iniciado:

- Web: `http://localhost:5667`
- Comprobación de salud: `http://localhost:5667/health`

Para detener los servicios usa `Ctrl+C`. Para bajarlos:

```bash
docker compose down
```

## Exponer la app con ngrok

Con los contenedores levantados:

```bash
ngrok http 5667
```

## Conexión a PostgreSQL

Puedes conectarte, por ejemplo desde DBeaver, con:

- Host: `localhost`
- Puerto: `5432`
- Base de datos: `checklectura`
- Usuario: `checklectura`
- Contraseña: `checklectura`

## Estructura del proyecto

- `backend/app/routes.py`: rutas HTTP, formularios y control de acceso.
- `backend/app/services.py`: lógica para planes, calendario y contexto de vistas.
- `backend/app/repository.py`: consultas y operaciones de planes, lecturas y métricas.
- `backend/app/db.py`: esquema, migraciones ligeras, semillas y catálogo de libros bíblicos.
- `backend/app/auth.py`: sesión, usuarios y acceso de administrador.
- `backend/app/i18n.py`: textos traducibles de la interfaz.
- `backend/app/templates/`: plantillas HTML Jinja.
- `backend/app/static/`: CSS y recursos estáticos.
- `docker-compose.yml`: servicios de PostgreSQL y backend.

## Rutas principales

- `/login`: inicio de sesión.
- `/signup`: creación de cuenta.
- `/plans`: listado y creación de planes.
- `/plans/{id}`: detalle, calendario y lecturas de un plan.
- `/plans/{id}/info`: progreso y estadísticas del plan.
- `/admin`: administración de usuarios.

## Datos y migraciones

La inicialización de la base de datos se ejecuta al arrancar el backend. Las ampliaciones del esquema y el catálogo de los 66 libros RV60 se mantienen en `backend/app/db.py`.

Al cambiar modelos, tablas o datos iniciales, reconstruye el backend para que se aplique la inicialización:

```bash
docker compose up --build
```

## Traducciones

Los textos de interfaz que no proceden de la base de datos están centralizados en `backend/app/i18n.py`.

Para añadir un idioma:

1. Añade su diccionario a `TRANSLATIONS`.
2. Añade los meses a `MONTH_TRANSLATIONS`.
3. Incorpora su opción y bandera en `backend/app/templates/base.html`.

Los títulos de planes, nombres de usuarios, notas y nombres de libros son datos de la base de datos y no se traducen automáticamente.
