# 🎯 Quiz Master

Quiz Master is a Flask-based web application that allows users to take quizzes and administrators to manage quiz content. It includes user authentication, quiz management, analytics, and email functionality. 🚀

## ✨ Features

### **🔑 Admin Portal**
- **🏠 Home**: Add quizzes by specifying chapter, duration, and date.
- **📚 Subjects**: Add, edit, and delete subjects.
- **📖 Chapters**: Sub-navbar displaying subjects, dynamically managed via JavaScript.
- **❓ Questions**: Manage MCQs (add, edit, and delete questions, options, and answers).
- **📊 Student Details**:
  - **🧑‍🎓 Personal Details**: Fetch user details from the database; admins can delete users.
  - **📈 Academic Details**: Displays:
    - 📊 Bar graphs showing the number of quizzes attempted per subject and the average marks.
    - 📄 A detailed transcript for each quiz taken by a user.
- **🔍 Search & 🚪 Logout**: Search functionality and logout option.

### **👩‍💻 User Portal**
- **🏠 Home**: Displays all subjects with descriptions and their respective chapters.
- **🎯 Live Quiz**:
  - Shows upcoming quizzes with details.
  - **👁️ View button**: Opens a modal with quiz details (date, duration, number of questions, etc.).
  - **📝 Attempt button**: Takes users to the quiz instructions page.
  - **🕒 Quiz Page**:
    - Timer and pause functionality (pauses screen activities until resumed).
    - Collects responses and displays results with a 📄 transcript and 📊 performance pie chart.
- **📬 Contact Page**: User-friendly contact form that automatically sends an email using Flask-Mail.
- **👤 User Details**:
  - Users can ✏️ edit their personal details.
  - Academic details include 📊 charts and 📄 transcripts specific to the user.
- **🔍 Search & 🚪 Logout**: Search functionality and logout option.

## 🛠️ Tech Stack
- **🖥️ Backend**: Flask, SQLAlchemy
- **🎨 Frontend**: HTML, CSS, JavaScript, Bootstrap, Jinja templating
- **🗄️ Database**: SQLite
- **📧 Email**: Flask-Mail

## ⚙️ Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quiz-master.git
   cd quiz-master
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables (for email functionality):
   ```bash
   export MAIL_USERNAME='your-email@example.com'
   export MAIL_PASSWORD='your-email-password'
   ```
5. Run the application:
   ```bash
   flask run
   ```
6. Open `http://127.0.0.1:8080/` in your browser. 🌍

## 🚀 Deployment
For free deployment, consider using platforms like **Render, Railway, or Vercel**.

## 📜 License
This project is licensed under the MIT License.

## 📞 Contact
For queries or contributions, feel free to reach out via email or GitHub issues. 💌
