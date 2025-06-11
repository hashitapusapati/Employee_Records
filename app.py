from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Employee, UploadHistory
from config import get_config
from datetime import datetime
import csv
import io
import logging
import os
import pytz

app = Flask(__name__, static_folder='.', static_url_path='')
app.config.from_object(get_config())
db.init_app(app)

# --- Print out the DB URI to confirm the correct configuration is loaded ---
print(f"Using SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")

# Configure CORS to allow multiple origins for development
# (Now including 127.0.0.1:5000 and localhost:5000, since Flask will run on port 5000)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5000",
                "http://localhost:5000"
            ]
        }
    }
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Timezone handling
app_timezone = os.getenv('APP_TIMEZONE', 'UTC')
try:
    tz = pytz.timezone(app_timezone)
except pytz.exceptions.UnknownTimeZoneError:
    logger.warning(f"Invalid timezone {app_timezone}, defaulting to UTC")
    tz = pytz.UTC

# Initialize database with constant employees
with app.app_context():
    db.create_all()
    if Employee.query.count() == 0:
        initial_employees = [
            {
                "name": "John Doe",
                "department": "IT",
                "joining_date": "2023-01-15",
                "salary": 60000,
                "status": "Active",
                "avatar_url": "https://uifaces.co/our-content/donated/1H_7AxP0.jpg"
            },
            {
                "name": "Jane Smith",
                "department": "HR",
                "joining_date": "2022-07-10",
                "salary": 55000,
                "status": "On Leave",
                "avatar_url": "https://uifaces.co/our-content/donated/bUkmHPKs.jpg"
            },
            {
                "name": "Alice Brown",
                "department": "Finance",
                "joining_date": "2023-03-20",
                "salary": 65000,
                "status": "Active",
                "avatar_url": "https://randomuser.me/api/portraits/women/1.jpg"
            },
            {
                "name": "Bob Johnson",
                "department": "Sales",
                "joining_date": "2022-11-05",
                "salary": 58000,
                "status": "Active",
                "avatar_url": "https://randomuser.me/api/portraits/men/2.jpg"
            },
            {
                "name": "Clara Lee",
                "department": "Marketing",
                "joining_date": "2023-06-12",
                "salary": 62000,
                "status": "On Leave",
                "avatar_url": "https://randomuser.me/api/portraits/women/3.jpg"
            },
            {
                "name": "David Kim",
                "department": "IT",
                "joining_date": "2021-09-01",
                "salary": 70000,
                "status": "Resigned",
                "avatar_url": "https://randomuser.me/api/portraits/men/4.jpg"
            },
            {
                "name": "Emma Davis",
                "department": "HR",
                "joining_date": "2023-08-15",
                "salary": 56000,
                "status": "Active",
                "avatar_url": "https://randomuser.me/api/portraits/women/5.jpg"
            }
        ]
        for emp in initial_employees:
            joining_date_obj = datetime.strptime(emp["joining_date"], '%Y-%m-%d').date()
            db.session.add(Employee(
                name=emp["name"],
                department=emp["department"],
                joining_date=joining_date_obj,
                salary=emp["salary"],
                status=emp["status"],
                avatar_url=emp["avatar_url"]
            ))
        db.session.commit()
        logger.debug(f"Initialized database with {len(initial_employees)} employees")

@app.route('/')
def index():
    return send_file('index.html')

VALID_STATUSES = ['Active', 'On Leave', 'Resigned']
VALID_DEPARTMENTS = ['HR', 'IT', 'Finance', 'Sales', 'Marketing']

def validate_employee_data(data):
    errors = []
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Name must be at least 2 characters long.')
    if not data.get('department') or data['department'] not in VALID_DEPARTMENTS:
        errors.append('Invalid or missing department.')
    if not data.get('joining_date'):
        errors.append('Joining date is required.')
    else:
        try:
            datetime.strptime(data['joining_date'], '%Y-%m-%d')
        except ValueError:
            errors.append('Joining date must be in YYYY-MM-DD format.')
    if not data.get('salary') or not isinstance(data.get('salary'), (int, float)) or data['salary'] < 0:
        errors.append('Salary must be a non-negative number.')
    if not data.get('status') or data['status'] not in VALID_STATUSES:
        errors.append('Invalid or missing status.')
    return errors

@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        query = Employee.query
        search = request.args.get('search', '').lower()
        departments = request.args.getlist('department')
        statuses = request.args.getlist('status')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        min_salary = request.args.get('min_salary')
        max_salary = request.args.get('max_salary')
        sort_by = request.args.get('sort_by', 'name-asc')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))

        # Only apply filters if they are actually provided with values
        if search and search.strip():
            query = query.filter(Employee.name.ilike(f'%{search}%'))
        if departments and any(d.strip() for d in departments):
            query = query.filter(Employee.department.in_(departments))
        if statuses and any(s.strip() for s in statuses):
            query = query.filter(Employee.status.in_(statuses))
        if from_date and from_date.strip():
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                query = query.filter(Employee.joining_date >= from_date_obj)
            except ValueError:
                logger.warning(f"Invalid from_date: {from_date}")
        if to_date and to_date.strip():
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                query = query.filter(Employee.joining_date <= to_date_obj)
            except ValueError:
                logger.warning(f"Invalid to_date: {to_date}")
        if min_salary and str(min_salary).strip():
            try:
                query = query.filter(Employee.salary >= int(min_salary))
            except ValueError:
                logger.warning(f"Invalid min_salary: {min_salary}")
        if max_salary and str(max_salary).strip():
            try:
                query = query.filter(Employee.salary <= int(max_salary))
            except ValueError:
                logger.warning(f"Invalid max_salary: {max_salary}")

        sort_field, sort_order = sort_by.split('-') if '-' in sort_by else (sort_by, 'asc')
        sort_column = {
            'name': Employee.name,
            'department': Employee.department,
            'joining': Employee.joining_date,
            'salary': Employee.salary,
            'status': Employee.status
        }.get(sort_field, Employee.name)
        query = query.order_by(sort_column.asc() if sort_order == 'asc' else sort_column.desc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        employees = [{
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'joiningDate': emp.joining_date.strftime('%Y-%m-%d'),
            'salary': emp.salary,
            'status': emp.status,
            'avatar_url': emp.avatar_url or 'https://via.placeholder.com/30'
        } for emp in paginated.items]

        result = {
            'employees': employees,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }
        logger.debug('GET /api/employees successful: %s', result)
        return jsonify(result)
    except Exception as e:
        logger.error('Error in GET /api/employees: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees', methods=['POST'])
def add_employee():
    try:
        data = request.get_json()
        errors = validate_employee_data(data)
        if errors:
            logger.warning('Validation errors in POST /api/employees: %s', errors)
            return jsonify({'errors': errors}), 400
        joining_date = datetime.strptime(data['joining_date'], '%Y-%m-%d').date()
        new_emp = Employee(
            name=data['name'].strip(),
            department=data['department'],
            joining_date=joining_date,
            salary=int(data['salary']),
            status=data['status'],
            avatar_url=data.get('avatar_url', 'https://via.placeholder.com/30')
        )
        db.session.add(new_emp)
        db.session.commit()
        result = {
            'id': new_emp.id,
            'name': new_emp.name,
            'department': new_emp.department,
            'joiningDate': new_emp.joining_date.strftime('%Y-%m-%d'),
            'salary': new_emp.salary,
            'status': new_emp.status,
            'avatar_url': new_emp.avatar_url
        }
        logger.debug('Employee added: %s', new_emp.name)
        return jsonify(result), 201
    except Exception as e:
        db.session.rollback()
        logger.error('Error in POST /api/employees: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    try:
        emp = Employee.query.get(employee_id)
        if not emp:
            logger.warning(f"Employee not found: {employee_id}")
            return jsonify({'error': 'Employee not found'}), 404
        data = request.get_json()
        errors = validate_employee_data(data)
        if errors:
            logger.warning('Validation errors in PUT /api/employees/%d: %s', employee_id, errors)
            return jsonify({'errors': errors}), 400
        emp.name = data['name'].strip()
        emp.department = data['department']
        emp.joining_date = datetime.strptime(data['joining_date'], '%Y-%m-%d').date()
        emp.salary = int(data['salary'])
        emp.status = data['status']
        emp.avatar_url = data.get('avatar_url', emp.avatar_url) or 'https://via.placeholder.com/30'
        db.session.commit()
        logger.debug('Employee updated: %s', emp.name)
        return jsonify({
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'joiningDate': emp.joining_date.strftime('%Y-%m-%d'),
            'salary': emp.salary,
            'status': emp.status,
            'avatar_url': emp.avatar_url
        })
    except Exception as e:
        db.session.rollback()
        logger.error('Error in PUT /api/employees/%d: %s', employee_id, str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        emp = Employee.query.get(employee_id)
        if not emp:
            logger.warning(f"Employee not found: {employee_id}")
            return jsonify({'error': 'Employee not found'}), 404
        db.session.delete(emp)
        db.session.commit()
        logger.debug('Employee deleted: %d', employee_id)
        return jsonify({'message': 'Employee deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error('Error in DELETE /api/employees/%d: %s', employee_id, str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.warning("No file provided in upload request")
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
        csv_reader = csv.DictReader(stream)
        required_fields = {'name', 'department', 'joining_date', 'salary', 'status'}
        if not all(field in csv_reader.fieldnames for field in required_fields):
            logger.warning("CSV missing required fields")
            return jsonify({'error': 'CSV missing required fields'}), 400

        employees = []
        for row in csv_reader:
            try:
                errors = validate_employee_data(row)
                if errors:
                    logger.warning(f"Invalid CSV row: {row}, errors: {errors}")
                    continue
                joining_date = datetime.strptime(row['joining_date'], '%Y-%m-%d').date()
                employee = Employee(
                    name=row['name'].strip(),
                    department=row['department'],
                    joining_date=joining_date,
                    salary=float(row['salary']),
                    status=row['status'],
                    avatar_url=row.get('avatar_url', 'https://via.placeholder.com/30')
                )
                employees.append(employee)
            except Exception as e:
                logger.warning(f"Error processing CSV row {row}: {str(e)}")
                continue

        if employees:
            db.session.bulk_save_objects(employees)
            upload_history = UploadHistory(filename=file.filename, timestamp=datetime.now(tz))
            db.session.add(upload_history)
            db.session.commit()
            logger.debug(f"CSV uploaded: {file.filename}, {len(employees)} employees added")
        return jsonify({'message': f'File {file.filename} uploaded successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error('Error in POST /api/upload: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_history', methods=['GET'])
def get_upload_history():
    try:
        uploads = UploadHistory.query.order_by(UploadHistory.timestamp.desc()).all()
        result = [{'name': u.filename, 'timestamp': u.timestamp.isoformat()} for u in uploads]
        logger.debug('Upload history retrieved: %d records', len(result))
        return jsonify(result)
    except Exception as e:
        logger.error('Error in GET /api/upload_history: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_employees():
    try:
        search = request.args.get('search', '')
        departments = request.args.getlist('department')
        statuses = request.args.getlist('status')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        min_salary = request.args.get('min_salary')
        max_salary = request.args.get('max_salary')

        query = Employee.query
        if search:
            query = query.filter(Employee.name.ilike(f'%{search}%'))
        if departments:
            query = query.filter(Employee.department.in_(departments))
        if statuses:
            query = query.filter(Employee.status.in_(statuses))
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                query = query.filter(Employee.joining_date >= from_date_obj)
            except ValueError:
                logger.warning(f"Invalid from_date in download: {from_date}")
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                query = query.filter(Employee.joining_date <= to_date_obj)
            except ValueError:
                logger.warning(f"Invalid to_date in download: {to_date}")
        if min_salary:
            try:
                query = query.filter(Employee.salary >= int(min_salary))
            except ValueError:
                logger.warning(f"Invalid min_salary in download: {min_salary}")
        if max_salary:
            try:
                query = query.filter(Employee.salary <= int(max_salary))
            except ValueError:
                logger.warning(f"Invalid max_salary in download: {max_salary}")

        employees = query.all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Department', 'Joining Date', 'Salary', 'Status', 'Avatar URL'])
        for emp in employees:
            writer.writerow([
                emp.id,
                emp.name,
                emp.department,
                emp.joining_date.strftime('%Y-%m-%d'),
                emp.salary,
                emp.status,
                emp.avatar_url or ''
            ])
        output.seek(0)
        logger.debug('CSV downloaded: %d employees', len(employees))
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='employees.csv'
        )
    except Exception as e:
        logger.error('Error in GET /api/download: %s', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/export', methods=['GET'])
def export_employees():
    return download_employees()

@app.route('/api/employees/find/<name>', methods=['GET'])
def find_employee_by_name(name):
    try:
        employees = Employee.query.filter(Employee.name.ilike(f'%{name}%')).all()
        result = [{
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'joiningDate': emp.joining_date.strftime('%Y-%m-%d'),
            'salary': emp.salary,
            'status': emp.status,
            'avatar_url': emp.avatar_url or 'https://via.placeholder.com/30'
        } for emp in employees]
        return jsonify(result)
    except Exception as e:
        logger.error('Error in GET /api/employees/find/%s: %s', name, str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/all', methods=['GET'])
def get_all_employees():
    try:
        employees = Employee.query.all()
        result = [{
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'joiningDate': emp.joining_date.strftime('%Y-%m-%d'),
            'salary': emp.salary,
            'status': emp.status,
            'avatar_url': emp.avatar_url or 'https://via.placeholder.com/30'
        } for emp in employees]
        return jsonify(result)
    except Exception as e:
        logger.error('Error in GET /api/employees/all: %s', str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    
    app.run(debug=True, port=5000)
