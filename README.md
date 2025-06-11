# 📋 Employee Records

A responsive and feature-rich **Flask web application** to manage employee data — built using **Flask**, **SQLAlchemy**, **CORS**, and supports upload/download functionalities.

---

### 🖼️ Preview

![Employee Records UI](b49c5a1c-feea-4b21-862c-f6ded70da3f1.png)

---

### 🚀 Features

- 🔍 Search employees by name
- 🔃 Filter by **Department**, **Status**, **Joining Date**, **Salary**
- 🗂️ Sort by various columns
- 📤 Upload employee data via CSV
- 📥 Download existing records
- ✏️ Edit/Delete employee data
- 📘 Tracks upload history
- 👩‍💼 Built with clean and modern UI design

---

### 🛠️ Tech Stack

- Backend: **Flask**, **SQLAlchemy**
- Frontend: **HTML**, **CSS**, **JavaScript**
- Database: **SQLite**
- Others: **CORS**, **Pytz**, **Logging**

---

### ⚙️ Setup Instructions

Follow these steps to set up and run the project locally:

| Command                         | Expected Outcome                         |
|--------------------------------|-------------------------------------------|
| `python -m venv venv`          | Creates a new `venv` folder               |
| `venv\Scripts\activate` (Win)  | Activates virtual environment             |
| `source venv/bin/activate` (Mac/Linux) | Activates virtual environment     |
| `pip install -r requirements.txt` | Installs all required packages         |
| `python app.py`                | Runs the application on `127.0.0.1:5000`  |

---

### 📁 Project Structure

```
├── app.py
├── models.py
├── config.py
├── templates/
├── static/
├── requirements.txt
├── README.md
```

---

### 📂 APIs Overview

| Endpoint         | Method | Description                        |
|------------------|--------|------------------------------------|
| `/employees`     | GET    | Fetch all employees                |
| `/upload`        | POST   | Upload CSV                        |
| `/download`      | GET    | Download all records               |
| `/employee/<id>` | PUT    | Update an employee                 |
| `/employee/<id>` | DELETE | Delete an employee                 |

---

### 📜 Author

Developed by **Hashita Pusapati**  
Feel free to reach out for contributions or questions.
