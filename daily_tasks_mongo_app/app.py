import os
from datetime import datetime, date
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')


def get_mongo_uri():
    mongo_url = os.getenv('MONGO_URL') or os.getenv('MONGODB_URL')
    if mongo_url:
        return mongo_url

    host = os.getenv('MONGOHOST')
    port = os.getenv('MONGOPORT', '27017')
    user = os.getenv('MONGOUSER')
    password = os.getenv('MONGOPASSWORD')

    if host and user and password:
        return f"mongodb://{user}:{password}@{host}:{port}/"
    if host:
        return f"mongodb://{host}:{port}/"

    return 'mongodb://localhost:27017/'


MONGO_URI = get_mongo_uri()
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'daily_tasks_db')

client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]
tasks = db['tasks']


@app.context_processor
def inject_now():
    return {'today_iso': date.today().isoformat()}


@app.route('/')
def home():
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    q = request.args.get('q', '').strip()

    query = {}
    if status == 'pending':
        query['completed'] = False
    elif status == 'done':
        query['completed'] = True

    if category != 'all':
        query['category'] = category

    if q:
        query['$or'] = [
            {'title': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}},
        ]

    task_list = list(tasks.find(query).sort([('completed', 1), ('task_date', 1), ('created_at', -1)]))

    total = tasks.count_documents({})
    pending = tasks.count_documents({'completed': False})
    done = tasks.count_documents({'completed': True})
    total_minutes = 0
    for item in tasks.find({'completed': False}, {'estimated_minutes': 1}):
        total_minutes += int(item.get('estimated_minutes', 0) or 0)

    return render_template(
        'index.html',
        tasks=task_list,
        total=total,
        pending=pending,
        done=done,
        total_minutes=total_minutes,
        current_status=status,
        current_category=category,
        current_query=q,
    )


@app.post('/add')
def add_task():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'Pessoal').strip() or 'Pessoal'
    priority = request.form.get('priority', 'Média').strip() or 'Média'
    task_date = request.form.get('task_date', '').strip() or date.today().isoformat()
    estimated_minutes = request.form.get('estimated_minutes', '0').strip()

    if not title:
        flash('O título da tarefa é obrigatório.', 'error')
        return redirect(url_for('home'))

    try:
        estimated_minutes = max(0, int(estimated_minutes or 0))
    except ValueError:
        estimated_minutes = 0

    document = {
        'title': title,
        'description': description,
        'category': category,
        'priority': priority,
        'task_date': task_date,
        'estimated_minutes': estimated_minutes,
        'completed': False,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }

    try:
        tasks.insert_one(document)
        flash('Tarefa adicionada com sucesso.', 'success')
    except PyMongoError:
        flash('Erro ao guardar a tarefa no MongoDB.', 'error')

    return redirect(url_for('home'))


@app.post('/toggle/<task_id>')
def toggle_task(task_id):
    try:
        task = tasks.find_one({'_id': ObjectId(task_id)})
        if task:
            tasks.update_one(
                {'_id': ObjectId(task_id)},
                {
                    '$set': {
                        'completed': not task.get('completed', False),
                        'updated_at': datetime.utcnow(),
                    }
                },
            )
            flash('Estado da tarefa atualizado.', 'success')
    except Exception:
        flash('Não foi possível atualizar a tarefa.', 'error')

    return redirect(url_for('home'))


@app.post('/delete/<task_id>')
def delete_task(task_id):
    try:
        tasks.delete_one({'_id': ObjectId(task_id)})
        flash('Tarefa removida.', 'success')
    except Exception:
        flash('Não foi possível remover a tarefa.', 'error')

    return redirect(url_for('home'))


@app.get('/api/tasks')
def api_tasks():
    data = []
    for item in tasks.find().sort([('completed', 1), ('task_date', 1), ('created_at', -1)]):
        data.append(
            {
                'id': str(item['_id']),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'category': item.get('category', ''),
                'priority': item.get('priority', ''),
                'task_date': item.get('task_date', ''),
                'estimated_minutes': item.get('estimated_minutes', 0),
                'completed': item.get('completed', False),
            }
        )
    return jsonify(data)


@app.get('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')


@app.get('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
