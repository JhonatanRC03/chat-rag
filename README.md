# Chat RAG - Proyecto Hackathon

## 📋 Descripción

Aplicación de Chat con funcionalidad RAG (Retrieval-Augmented Generation) construida con FastAPI (backend) y React + TypeScript + Vite (frontend).

## 🏗️ Arquitectura del Proyecto

```
chat-rag/
├── backend/                 # FastAPI Backend
└── frontend/                # React + TypeScript Frontend
```

---

## 🔧 Backend (FastAPI)

### Estructura del Backend

```
backend/
├── main.py                  # Punto de entrada principal con FastAPI app
├── requirements.txt         # Dependencias de Python
├── .env                    # Variables de entorno
├── README.md               # Documentación del backend
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── main.py         # Router principal con logging
    │   └── routes/         # Endpoints de la API
    │       ├── __init__.py
    │       └── version.py  # API de versión (ejemplo)
    ├── core/
    │   ├── __init__.py
    │   ├── config.py       # Configuración con pydantic-settings
    │   └── database.py     # Inicialización de base de datos
    ├── models/             # Modelos de base de datos
    │   └── __init__.py
    ├── schemas/            # Esquemas de Pydantic (DTOs)
    │   └── __init__.py
    ├── services/           # Lógica de negocio
    │   └── __init__.py
    ├── utils/              # Utilidades y helpers
    │   └── __init__.py
    └── modules/            # Módulos específicos de funcionalidad
        └── __init__.py
```

### Tecnologías Backend

- **FastAPI**: Framework web moderno y rápido
- **Uvicorn**: Servidor ASGI
- **Pydantic**: Validación de datos y configuración
- **Python 3.9+**: Lenguaje base

### Configuración del Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8083
```

### Endpoints Disponibles

- `GET /api/v1/version/` - Información de versión
- `GET /docs` - Documentación automática de FastAPI
- `GET /redoc` - Documentación alternativa

---

## 🎨 Frontend (React + TypeScript)

### Estructura del Frontend

```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── ui/             # Componentes básicos (Button, Input, Modal)
│   │   └── layout/         # Componentes de layout (Header, Footer, Sidebar)
│   ├── pages/              # Páginas/Vistas de la aplicación
│   ├── hooks/              # Custom hooks de React
│   ├── services/           # Servicios para APIs y lógica externa
│   ├── types/              # Definiciones de TypeScript
│   ├── utils/              # Funciones utilitarias y helpers
│   ├── store/              # Estado global (Zustand, Redux, Context)
│   ├── constants/          # Constantes de la aplicación
│   ├── assets/            # Imágenes, íconos, archivos estáticos
│   ├── App.tsx            # Componente principal
│   ├── main.tsx           # Punto de entrada
│   └── index.css          # Estilos globales
├── public/                 # Archivos públicos estáticos
├── package.json           # Dependencias y scripts
├── vite.config.ts         # Configuración de Vite
├── tsconfig.json          # Configuración de TypeScript
└── eslint.config.js       # Configuración de ESLint
```

### Tecnologías Frontend

- **React 19**: Biblioteca de UI
- **TypeScript**: Tipado estático
- **Vite**: Build tool y dev server
- **ESLint**: Linting de código

### Configuración del Frontend

```bash
cd frontend
npm install
npm run dev
```

### Scripts Disponibles

- `npm run dev` - Servidor de desarrollo
- `npm run build` - Build de producción
- `npm run preview` - Preview del build
- `npm run lint` - Linting del código

---

## 🚀 Desarrollo

### Orden de Ejecución

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8083
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### URLs de Desarrollo

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8083
- **Documentación API**: http://localhost:8083/docs



## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.