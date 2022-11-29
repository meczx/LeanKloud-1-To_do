from flask import Flask, request
from flask_restplus import Api, Resource, fields
import mysql.connector
import datetime


# database connection

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="bharathi02",
    database="lk_task_db"
)

app = Flask(_name_)
api = Api(app, version='1.0', title='TodoMVC API', description='A simple TodoMVC API', )
ns = api.namespace('todos', description='TODO operations')
todo = api.model('Todo',
                 {
                     'status': fields.String(required=True, description='The status of the task'),
                     'id': fields.Integer(readonly=True, description='The task unique identifier'),
                     'task': fields.String(required=True, description='The task details'),
                     'dueby': fields.Date(required=True, description='The task due date'),

                 }
                 )


class TodoDAO(object):
    def _init_(self):
        self.counter = 0

    def add_task(self, task, dueby, status):
        self.counter += 1
        cursor = mydb.cursor()
        query = 'insert into todos values (%s, %s, %s, %s)'
        value = (self.counter, task, dueby, status)
        cursor.execute(query, value)
        mydb.commit()

    def get_task(self, id):
        cursor = mydb.cursor()
        query = 'select * from todos where id = %s'
        value = (id,)
        cursor.execute(query, value)
        result = cursor.fetchall()
        if len(result) == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))
        else:
            return {'id': result[0][0], 'task': result[0][1], 'dueby': result[0][2].strftime('%Y-%m-%d'),
                    'status': result[0][3]}

    def delete_task(self, id):
        cursor = mydb.cursor()
        query = 'delete_task from todos where id = %s'
        value = (id,)
        cursor.execute(query, value)
        mydb.commit()
        if cursor.rowcount == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))

    def all_tasks(self):
        cursor = mydb.cursor()
        query = 'select * from todos'
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) == 0:
            api.abort(404, "No Todo exists".format(id))
        else:
            result = [{'id': result[i][0], 'task': result[i][1], 'dueby': result[i][2].strftime('%Y-%m-%d'),
                       'status': result[i][3]} for i in range(len(result))]
            return result

    def get_due_for_task(self, due_by):
        cursor = mydb.cursor()
        query = 'select * from todos where dueby = %s and status != %s'
        value = (due_by, "Finished")
        cursor.execute(query, value)
        result = cursor.fetchall()
        if len(result) == 0:
            api.abort(404, "No over_dues")
        else:
            result = [{'id': result[i][0], 'task': result[i][1], 'dueby': result[i][2].strftime('%Y-%m-%d'),
                       'status': result[i][3]} for i in range(len(result))]
            return result

    def over_dues(self):
        curdate = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor = mydb.cursor()
        query = 'select * from todos where dueby < %s and status != %s'
        value = (curdate, "Finished")
        cursor.execute(query, value)
        result = cursor.fetchall()
        if len(result) == 0:
            api.abort(404, "No over_dues")
        else:
            result = [{'id': result[i][0], 'task': result[i][1], 'dueby': result[i][2].strftime('%Y-%m-%d'),
                       'status': result[i][3]} for i in range(len(result))]
            return result

    def tasks_done(self):
        cursor = mydb.cursor()
        query = 'select * from todos where status = %s'
        value = ("Finished",)
        cursor.execute(query, value)
        result = cursor.fetchall()
        if len(result) == 0:
            api.abort(404, "No Todo exists")
        else:
            result = [{'id': result[i][0], 'task': result[i][1], 'dueby': result[i][2].strftime('%Y-%m-%d'),
                       'status': result[i][3]} for i in range(len(result))]
            return result

    def update_status_of_task(self, id, status):
        cursor = mydb.cursor()
        query = 'update todos set status = %s where id = %s'
        value = (status, id)
        cursor.execute(query, value)
        mydb.commit()
        if cursor.rowcount == 0:
            api.abort(404, "Todo {} doesn't exist".format(id))


DAO = TodoDAO()


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''

    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get_task(self):
        '''List all tasks'''
        todos = DAO.all_tasks()
        return todos

    @ns.doc('create_todo', security='apikey')
    @ns.response(204, 'Todo added')
    @ns.param('task', 'The task to be done')
    @ns.param('status', 'Status of the task (Not Started, In Process, Finished)',
              enum=["Not Started", "In Process", "Finished"])
    @ns.param('due_by', "The task's due date")
    def post(self):
        '''Add a new task'''
        task = request.values.get_task('task')
        status = request.values.get_task('status')
        due_by = request.values.get_task('due_by')
        DAO.add_task(task, due_by, status)
        return '', 204


@ns.route('/status')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The id of the task')
@ns.param('status', 'Status to be updated', enum=["Not Started", "In Process", "Finished"])
class UpdateTask(Resource):
    @ns.doc('status_update', security='apikey')
    @ns.response('204', 'Todo updated')
    def post(self):
        id = int(request.values.get_task('id'))
        status = request.values.get_task('status')
        DAO.update_status_of_task(id, status)
        return '', 204


@ns.route('/over_dues')
@ns.response(404, 'Todo not found')
class over_dues(Resource):
    @ns.doc('todo_overdue')
    @ns.marshal_list_with(todo)
    def get_task(self):
        return DAO.over_dues()


@ns.route('/due')
@ns.response(404, 'Todo not found')
@ns.param('due_by', 'The due date')
class Due(Resource):
    @ns.doc('todo_due')
    @ns.marshal_list_with(todo)
    def get_task(self):
        due_by = request.values.get_task('due_by')
        return DAO.get_due_for_task(due_by)


@ns.route('/finished')
@ns.response(404, 'Todo not found')
class Finished(Resource):
    @ns.doc('finished_todo')
    @ns.marshal_list_with(todo)
    def get_task(self):
        return DAO.tasks_done()


@ns.route('/todo')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get_task(self):
        id = int(request.values.get_task('id'))
        return DAO.get_task(id)

    @ns.doc('delete_todo', security='apikey')
    @ns.response(204, 'Todo deleted')
    def delete_task(self):
        id = int(request.values.get_task('id'))
        DAO.delete_task(id)
        return '', 204


if _name_ == '_main_':
    app.run(debug=True)