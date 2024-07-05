from flask import Flask, render_template, send_file, request
from main import login_and_scrape  # Import your function from the script file

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['GET'])
def download():
    email = request.args.get('email')
    password = request.args.get('password')
    
    ics_file_path = login_and_scrape(email, password)
    
    if ics_file_path:
        return send_file(ics_file_path, as_attachment=True)
    else:
        return "Failed to generate iCalendar file."

if __name__ == '__main__':
    app.run(debug=True)