# 🌐 MediCare — Modern Healthcare Management Website
**Built with Django | Tailwind CSS | HTML**

A clean, responsive, and modern healthcare management platform designed to simplify patient interaction, appointment handling, and medical record access. MediCare focuses on a seamless user experience, fast performance, and secure backend logic using Django.

---

## 🚀 Features

- **User Authentication** (Login / Register)
- **Doctor & Patient Dashboard**
- **Appointment Booking System**
- **Responsive UI using Tailwind CSS**
- **Medical Records Management**
- **Admin Panel for Full Control**
- **Clean & Minimalist UI**
- **Secure Django Backend**

---

## 🛠️ Tech Stack

| Technology        | Description                  |
|------------------|------------------------------|
| **Django**       | Backend Framework            |
| **Tailwind CSS** | Styling & Responsive Design  |
| **HTML5**        | UI Structure                 |
| **SQLite / PostgreSQL** | Database (customizable) |

---

## 📸 Screenshots

> Add your project screenshots inside the `screenshots/` folder  
> Replace these paths with your actual images


---

## 📦 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/medicare.git
cd medicare
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / MacOS**
```bash
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Apply Migrations
```bash
python manage.py migrate
```

### 5️⃣ Start Development Server
```bash
python manage.py runserver
```

Now open in browser:
👉 http://127.0.0.1:8000/

---

## 📁 Project Structure
```
medicare/
│── manage.py
│── requirements.txt
│── README.md
│
├── medicare/              # Main Django settings
├── users/                 # User authentication app
├── appointments/          # Appointment module
├── dashboard/             # User/Doctor dashboards
└── static/                # Tailwind + static files
```

---

## 🎨 TailwindCSS Integration

TailwindCSS is used for:
- Modern responsive UI
- Utility-first styling
- Faster development workflow

If using Tailwind CLI, watch file changes:
```bash
npm run dev
```

---

## 🤝 Contribution

Contributions are always welcome!
Feel free to open issues or submit pull requests.

---

## 🧑‍💻 Author

Nitish Kumar  
Made with ❤️ using Django & TailwindCSS.
```
