# ⚡ OmniDesk AI – Smart IT Ticket Management System

A **smart assistant for IT ticket management** that consolidates tickets from multiple sources (GLPI, SAP Solution Manager, Email, SMS) into one **unified web application**.  
The system uses **AI (Claude + custom models)** to classify, prioritize, and auto-respond to employee issues, while IT staff manage escalations through a **real-time analytics dashboard**.

## 🚀 Vision

POWERGRID employees are drowning in ticket chaos across multiple systems.  
OmniDesk AI fixes this by:
- **Unified Ticket Management**: Collecting tickets from multiple sources into one place
- **Smart Language Detection**: Real-time detection of English/Hindi mixed content
- **AI-Powered Responses**: Auto-classifying and suggesting instant solutions
- **Intelligent Escalation**: Forwarding unresolved issues to IT staff with full context
- **Live Analytics**: Providing IT teams with real-time dashboard and insights

## 🎯 Core Features

### Multi-Channel Ticket Intake
- **Web Portal**: Modern, responsive ticket submission interface
- **Email Integration**: Automatic email-to-ticket conversion
- **SMS Support**: Twilio-powered SMS ticket creation
- **GLPI Integration**: Direct integration with existing GLPI systems
- **SAP Solution Manager**: Enterprise-grade ticket synchronization

### AI-Powered Intelligence
- **Smart Classification**: Automatic categorization using Claude AI
- **Urgency Detection**: Intelligent priority assignment
- **Multi-Language Support**: Native Hindi/English mixed language processing
- **Instant Responses**: Context-aware automated solutions
- **Semantic Search**: Vector-based similar ticket discovery

### Advanced Analytics
- **Real-time Dashboard**: Live ticket metrics and KPIs
- **Performance Analytics**: Resolution times, success rates, trends
- **Category Insights**: Ticket distribution and pattern analysis
- **Team Performance**: Agent productivity and workload distribution
- **Predictive Analytics**: Proactive issue identification

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS with custom components
- **UI Components**: Chakra UI + Radix UI
- **3D Graphics**: Three.js for enhanced visualizations
- **State Management**: React hooks with custom state management
- **Charts**: Recharts for analytics visualization

### Backend
- **Framework**: FastAPI with Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: Qdrant for semantic search
- **Caching**: Redis for session and cache management
- **AI Services**: Anthropic Claude API
- **Background Tasks**: Celery with Redis broker
- **API Documentation**: Automatic OpenAPI/Swagger generation

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development
- **Database**: PostgreSQL 15 with connection pooling
- **Monitoring**: Built-in health checks and logging
- **Deployment**: Production-ready with environment configs

## 📋 Prerequisites

- **Node.js**: v18+ with npm/yarn
- **Python**: 3.9+ with pip
- **PostgreSQL**: 15+ (local or cloud)
- **Redis**: 7+ for caching
- **Qdrant**: Vector database instance
- **Docker**: For containerized deployment
- **Anthropic API Key**: For AI features

## 🏗 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ticket-agent.git
cd ticket-agent
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: DATABASE_URL, ANTHROPIC_API_KEY
nano .env
```

### 3. Docker Deployment (Recommended)
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Manual Setup (Development)

#### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
python -m app.main
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnidesk

# AI Services
ANTHROPIC_API_KEY=your_anthropic_key

# Vector Database
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=your_secure_secret_key
```

### Optional Integrations
```bash
# Email
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# GLPI
GLPI_URL=https://your-glpi-instance.com
GLPI_USER_TOKEN=your_glpi_token
```

## 📊 Demo Workflow

1. **Ticket Creation**: User submits issue via web, email, or SMS
2. **AI Processing**: System detects language, categorizes, and prioritizes
3. **Instant Response**: AI provides immediate solution in user's language
4. **IT Escalation**: Unresolved tickets forwarded to IT team with context
5. **Real-time Updates**: Dashboard reflects all changes and metrics
6. **Resolution Tracking**: Complete ticket lifecycle management

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Tests
```bash
# Start services
docker-compose up -d

# Run E2E tests
npm run test:e2e
```

## 🚀 Production Deployment

### Docker Production
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Cloud Deployment
- **Frontend**: Deploy to Vercel/Netlify
- **Backend**: Deploy to Railway/Heroku/AWS
- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **Vector DB**: Qdrant Cloud or self-hosted

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health

# Database status
curl http://localhost:8000/health/db

# AI service status
curl http://localhost:8000/health/ai
```

### Logs
```bash
# View application logs
docker-compose logs -f backend

# Monitor specific service
docker-compose logs -f qdrant
```

### Backup
```bash
# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Vector database backup
curl -X POST "http://localhost:6333/collections/{collection_name}/snapshots"
```

## 🛡 Security

- **Authentication**: JWT-based with secure token handling
- **Authorization**: Role-based access control
- **Data Encryption**: TLS/SSL for all communications
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API rate limiting and DDoS protection
- **Security Headers**: CORS, CSP, and security headers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript/Python type hints
- Write comprehensive tests
- Update documentation
- Use conventional commit messages
- Ensure CI/CD passes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude AI API
- **Qdrant** for vector search capabilities
- **FastAPI** for the excellent Python framework
- **Next.js** for the powerful React framework
- **POWERGRID** for the inspiration and use case

## 📞 Support

- **Documentation**: Check our [Wiki](../../wiki)
- **Issues**: Report bugs on [GitHub Issues](../../issues)
- **Discussions**: Join [GitHub Discussions](../../discussions)
- **Email**: support@omnidesk.ai

---

**Built with ❤️ for POWERGRID IT Teams**
