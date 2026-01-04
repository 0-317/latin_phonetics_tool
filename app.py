from flask import Flask, render_template, request
from project.hexingongneng import process_latin_text

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    latin_result = []
    if request.method == 'POST':
        input_content = request.form.get('latin_text', '').strip()
        latin_result = process_latin_text(input_content)
        print("Результат, сгенерированный сервером：", latin_result)
    return render_template('index.html', result=latin_result)

if __name__ == '__main__':
    app.run(debug=True)