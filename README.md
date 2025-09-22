# VitiGenLabs - Genetic Analysis Backend

A high-performance REST API backend for genetic analysis of grape varieties, built with FastAPI, MongoDB, and RabbitMQ. This system enables researchers to upload, process, and analyze VCF (Variant Call Format) files for grape genetic research.

## Features

### Core Functionality
- **VCF File Processing**: Upload and parse large VCF files with efficient memory management
- **Gene Search & Filtering**: Advanced search capabilities with pagination and real-time filtering
- **User Authentication**: JWT-based authentication with security key verification
- **Email Notifications**: Automated security key delivery via Brevo integration
- **Asynchronous Processing**: High-performance async operations for scalability

### Technical Highlights
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **MongoDB Integration**: Scalable NoSQL database with optimized indexing
- **RabbitMQ Messaging**: Reliable message queuing for email notifications
- **Security Features**: Bcrypt password hashing, JWT tokens, and email verification
- **Error Handling**: Comprehensive error handling and logging throughout the application

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   MongoDB       │    │   RabbitMQ      │
│   Web Server    │◄──►│   Database      │    │   Message Queue │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                              ▲
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│   File Upload   │                          │   Brevo         │
│   Processing    │                          │   Email Service │
└─────────────────┘                          └─────────────────┘
```

## API Endpoints

### Authentication
- `POST /api/v1/users/register` - User registration
- `POST /api/v1/users/login` - User authentication
- `POST /api/v1/users/verify-security-key` - Security key verification

### File Management
- `POST /api/v1/upload/upload` - Upload VCF files for processing
- `GET /api/v1/upload/uploaded-files` - List uploaded files

### Gene Search
- `GET /api/v1/search/` - Search genes with filtering and pagination

### Health Check
- `GET /` - API status and information
- `GET /health` - Health check endpoint

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- MongoDB 4.4 or higher
- RabbitMQ 3.8 or higher
- Brevo account (for email notifications)

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=vitigenlabs

# Security Configuration
SECRET_KEY=your-super-secret-key-here-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# File Upload Configuration
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=5368709120

# Email Configuration (Brevo)
BREVO_API_KEY=your-brevo-api-key-here
BREVO_SENDER_EMAIL=noreply@yourdomain.com
BREVO_SENDER_NAME=Your Name
```

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/JhonierSerna14/Frontend-VitiGenLabs.git
   cd vitigenlabs-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration values
   ```

5. **Start supporting services**
   ```bash
   # Start MongoDB (varies by installation)
   mongod
   
   # Start RabbitMQ (varies by installation)
   rabbitmq-server
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Development

### Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application setup
│   ├── config.py            # Configuration management
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py       # Database connection management
│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   ├── user.py          # User-related models
│   │   └── gene.py          # Gene-related models
│   ├── routes/              # API route handlers
│   │   ├── __init__.py
│   │   ├── user.py          # Authentication endpoints
│   │   ├── gene_search.py   # Gene search endpoints
│   │   └── file_upload.py   # File upload endpoints
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py              # Authentication service
│   │   ├── gene_search_service.py       # Gene search service
│   │   ├── file_processor.py            # File processing service
│   │   └── security_key_consumer.py     # Email notification service
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── FileStorageService.py        # File storage utilities
│       └── VCFParserService.py          # VCF file parsing utilities
├── uploads/                 # File upload directory
├── requirements.txt         # Python dependencies
├── run.py                  # Application entry point
├── .env                    # Environment variables (create from .env.example)
├── .gitignore             # Git ignore patterns
└── README.md              # This file
```

### API Documentation

Once the application is running, comprehensive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Code Quality

The codebase follows these standards:
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings for all modules and functions
- **Error Handling**: Robust error handling with proper logging
- **Security**: Secure password hashing, JWT tokens, and input validation
- **Performance**: Async/await patterns for optimal performance

## Usage Examples

### User Registration
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "researcher@example.com",
       "password": "SecurePassword123!"
     }'
```

### File Upload
```bash
curl -X POST "http://localhost:8000/api/v1/upload/upload" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@sample.vcf"
```

### Gene Search
```bash
curl -X GET "http://localhost:8000/api/v1/search/?search=PASS&page=1&per_page=25&collection_name=genes_123456789" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Performance Considerations

### File Processing
- **Chunked Processing**: Large VCF files are processed in chunks to manage memory usage
- **Parallel Processing**: Multi-core CPU utilization for parsing operations
- **Database Indexing**: Optimized indexes for fast gene searches
- **Async Operations**: Non-blocking I/O for better concurrency

### Scalability
- **Connection Pooling**: Efficient MongoDB connection management
- **Message Queuing**: RabbitMQ for reliable email processing
- **Pagination**: Efficient pagination for large result sets
- **Caching Ready**: Architecture prepared for Redis caching layer

## Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Password Security**: Bcrypt hashing with salt
- **Security Keys**: Email-based verification system
- **Token Expiration**: Configurable token lifetime

### Data Protection
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: MongoDB's natural protection
- **CORS Configuration**: Controlled cross-origin requests
- **File Type Validation**: Restricted file upload types

## Monitoring & Logging

### Logging
- **Structured Logging**: Consistent log format across modules
- **Log Levels**: Configurable logging levels
- **Error Tracking**: Comprehensive error logging with context
- **Performance Monitoring**: Request timing and performance metrics

### Health Checks
- **Database Connectivity**: MongoDB connection monitoring
- **Queue Health**: RabbitMQ connection status
- **Service Status**: Overall application health endpoint

**VitiGenLabs** - Advancing grape genetics research through modern technology.


⚡ Desarrollado con Python y ❤️

🌟 ¡Dale una estrella si te gusta el proyecto! ⭐