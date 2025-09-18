# ⚡ OmniDesk AI – Smart IT Ticket Hub  

A **smart assistant for IT ticket management** that consolidates tickets from multiple sources (GLPI, Solman, Email, SMS) into one **uniform web app**.  
The system uses **AI (Claude + custom models)** to classify, prioritize, and auto-respond to employee issues, while IT staff manage escalations through a **real-time analytics dashboard**.  

---

## 🚀 Vision  
POWERGRID employees are drowning in ticket chaos.  
OmniDesk AI fixes this by:  
- Collecting tickets from multiple sources into one place  
- Detecting language (English/Hindi mix) in real-time  
- Auto-classifying and suggesting instant solutions  
- Escalating unresolved issues to IT staff with full context  
- Providing IT with a live dashboard of all tickets  

---

## 🎯 Core Features (Prototype)  
- Multi-platform ticket intake (GLPI, Solman, Email, SMS)  
- AI classification + urgency detection (Claude API)  
- Multi-language instant auto-responses  
- Forwarding unresolved tickets to IT staff  
- Real-time analytics dashboard (counts, categories, resolution times, success rate)  
- Uniform, professional web UI (Next.js + Tailwind, mobile-friendly)  
- Ticket storage in **Neon (Postgres)** + semantic search in **Qdrant**  

---

## 🛠 Tech Stack  
- **Frontend**: Next.js + Tailwind  
- **Backend**: FastAPI (Python)  
- **Database**: Neon (Postgres, local connect)  
- **Vector DB**: Qdrant  
- **AI**: Claude API + custom Minkowski norm model (Hindi/English detection)  
- **Language Detection**: TensorFlow.js (runs in browser)  
- **Deployment**: Vercel (frontend), Railway (backend)  
- **Dev Tools**: VS Code (Kubernetes, Windsurf, Sixth extensions), WSL2  

---

## 👥 Team Roles (3 Members)  

**👩‍💻 Frontend Engineer**  
- Build Next.js web app with Tailwind  
- Chat-style ticket submission view + dashboard UI  
- Integrate real-time updates (WebSocket/Supabase)  
- Ensure responsive, uniform design  

**🧑‍💻 Backend Engineer**  
- FastAPI endpoints for ticket intake, AI responses, and analytics  
- Connect Claude API for classification + solutions  
- Integrate Qdrant for semantic search  
- Handle GLPI, Solman, email, and SMS ingestion  

**👨‍💻 Database & AI Ops**  
- Design Neon (Postgres) schema for tickets  
- Configure Qdrant vector embeddings  
- Set up TensorFlow.js language detection model  
- Manage deployments (Vercel + Railway) and environments  

---

## 🔗 Integration Workflow  

1. **Shared GitHub Repo**  
   - Repo contains `frontend/`, `backend/`, and `db/` folders.  
   - Each developer works on feature branches.  

2. **Common Data Contract**  
   - JSON schema for tickets defined early.  
   - Example:  
     ```json
     {
       "id": "123",
       "source": "email",
       "text": "VPN nahi chal raha",
       "language": "Hindi+English",
       "category": "Network/VPN",
       "urgency": "High",
       "ai_response": "Try resetting your VPN connection...",
       "status": "open",
       "created_at": "...",
       "updated_at": "..."
     }
     ```  

3. **API Stubs First**  
   - Backend exposes dummy endpoints for early frontend integration.  

4. **CI/CD**  
   - Auto-deploy with Vercel (frontend) + Railway (backend).  
   - GitHub Actions for linting + tests.  

5. **Final Merge**  
   - Frontend connects to FastAPI backend.  
   - Backend connects to Neon + Qdrant.  
   - End-to-end ticket flow tested with mock + real data.  

---

## 📊 Demo Flow  
1. User raises a ticket via Email/GLPI/SMS.  
2. AI detects language + urgency + category.  
3. AI responds instantly with solution in user’s language.  
4. Ticket + AI notes forwarded to IT staff.  
5. Dashboard updates with live metrics.  
6. IT staff can send updates/resolutions back to the user.  

---

## 🌱 Future Roadmap  
- Full GLPI + Solman API integrations  
- Mobile apps (iOS + Android)  
- Workflow automation (n8n)  
- SLA analytics + predictive resolution  
- Multi-channel support (WhatsApp, Teams, Slack)  
- Role-based access for IT managers/agents  
- Dark mode toggle  
- AI reasoning/explanation panel  

---

## 🏗 Setup (Prototype)  

### Prerequisites  
- Node.js (v18+)  
- Python 3.9+  
- Neon Postgres instance  
- Qdrant instance  
- Vercel + Railway accounts  

### 1. Clone Repo  
```bash
git clone https://github.com/yourusername/omni-desk-ai.git
cd omni-desk-ai
