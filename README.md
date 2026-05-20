# MedHelp

MedHelp is a full-stack medical appointment platform where patients can find doctors, book appointments, receive notifications, and use an AI chatbot for symptom guidance and doctor discovery.

👉 **Live App:** https://med-help-nine.vercel.app/

---

## Demo Credentials

Use these accounts to test the deployed app:

| Role | Email | Password |
|---|---|---|
| Patient | patient.aarav@medhelp.demo | Demo@12345 |
| Doctor | doctor.cardio@medhelp.demo | Demo@12345 |
| Admin | admin@medhelp.demo | Demo@12345 |

---

## Features

### Patient
- Register and login securely.
- Browse verified doctors.
- Search doctors by name or specialization.
- Book appointments with available doctors.
- View appointment status.
- Receive real-time notifications.
- Use the AI chatbot for symptom guidance and doctor discovery.

### Doctor
- Set available days and time slots.
- View pending appointment requests.
- Accept or reject appointments.
- Receive notifications when patients request appointments.

### Admin
- View all users.
- Review doctor applications.
- Approve or reject doctor requests.
- Manage users and doctors.

### AI Chatbot
- Understands patient symptoms.
- Suggests the right specialist.
- Searches available doctors from the database.
- Uses LangGraph for agent workflow.
- Uses RAG for symptom-to-specialist guidance.
- Uses MCP server to expose doctor tools.

---

## Screenshots
<img width="1906" height="865" alt="Screenshot 2026-05-20 192550" src="https://github.com/user-attachments/assets/cb09250a-1259-4a98-ac66-2a7e773d2256" />

<img width="1909" height="857" alt="Screenshot 2026-05-20 192856" src="https://github.com/user-attachments/assets/5caaa2be-ca30-4692-8e64-a620bc36216b" />

<img width="1904" height="858" alt="Screenshot 2026-05-20 192916" src="https://github.com/user-attachments/assets/78dd12f4-b655-48f5-826a-aac6590fd067" />

<img width="1899" height="861" alt="Screenshot 2026-05-20 193039" src="https://github.com/user-attachments/assets/2715a3c2-db55-4e1a-8a95-4265a9e6350e" />

<img width="1909" height="857" alt="Screenshot 2026-05-20 193150" src="https://github.com/user-attachments/assets/adfab674-b6e9-4aee-b868-59aa7f23e0d1" />

<img width="1913" height="862" alt="Screenshot 2026-05-20 193206" src="https://github.com/user-attachments/assets/c391eb72-ac65-4f84-ac18-427720caf250" />

<img width="1911" height="863" alt="Screenshot 2026-05-20 193323" src="https://github.com/user-attachments/assets/70c50533-9f3f-4484-a7b3-0e9861e38840" />

<img width="1910" height="861" alt="Screenshot 2026-05-20 193432" src="https://github.com/user-attachments/assets/3b8e29d5-d8c4-42e7-9582-009b83af0b11" />

<img width="1908" height="861" alt="Screenshot 2026-05-20 193526" src="https://github.com/user-attachments/assets/a8723941-3484-45f7-85a1-b3b76b22896f" />

<img width="1902" height="862" alt="Screenshot 2026-05-20 193546" src="https://github.com/user-attachments/assets/8de52f90-4605-4bb9-8e4e-b47c92cb5e3a" />

<img width="1907" height="857" alt="Screenshot 2026-05-20 193558" src="https://github.com/user-attachments/assets/4d6c94ed-65af-4e37-b5f0-136087a79979" />

<img width="1903" height="859" alt="Screenshot 2026-05-20 193704" src="https://github.com/user-attachments/assets/8a40c17b-5d75-4859-bd45-a27de36a185e" />

<img width="1911" height="859" alt="Screenshot 2026-05-20 193748" src="https://github.com/user-attachments/assets/0de1defe-b44d-4b64-bb3c-307f94daa063" />

---

## Tech Stack

### Frontend
- React
- TypeScript
- Redux Toolkit
- Vite
- CSS

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- WebSockets
- Cloudinary

### AI
- LangGraph
- LangChain
- Groq LLaMA models
- RAG with ChromaDB
- Sentence Transformers
- MCP Server

### Deployment
- Frontend: Vercel
- Backend API: Render
- MCP Server: Render
- Database: Neon PostgreSQL
- Docker
