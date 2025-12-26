from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import User, Vehicle, Maintenance, Repair, MileageLog, UserRole, VehicleType, MaintenanceType, RepairStatus
from app.utils import validate_vin, predict_next_maintenance, get_maintenance_status, calculate_daily_mileage
from app.email_utils import send_maintenance_notification, send_repair_notification
from datetime import datetime, date, timedelta
import json

api_bp = Blueprint('api', __name__)
web_bp = Blueprint('web', __name__)

# ============ API Routes ============

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Аутентификация пользователя"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password) or not user.is_active:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role.value}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@api_bp.route('/auth/register', methods=['POST'])
@jwt_required()
def register():
    """Регистрация нового пользователя (только для админов)"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'driver')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=username,
        email=email,
        role=UserRole[role.upper()],
        full_name=data.get('full_name')
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created', 'user': user.to_dict()}), 201

# Vehicles API
@api_bp.route('/vehicles', methods=['GET'])
@jwt_required()
def get_vehicles():
    """Получение списка транспортных средств"""
    vehicles = Vehicle.query.all()
    return jsonify([v.to_dict() for v in vehicles]), 200

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['GET'])
@jwt_required()
def get_vehicle(vehicle_id):
    """Получение информации о транспортном средстве"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return jsonify(vehicle.to_dict()), 200

@api_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def create_vehicle():
    """Создание нового транспортного средства"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if not validate_vin(data.get('vin')):
        return jsonify({'error': 'Invalid VIN number'}), 400
    
    if Vehicle.query.filter_by(vin=data['vin']).first():
        return jsonify({'error': 'VIN already exists'}), 400
    
    if Vehicle.query.filter_by(reg_number=data['reg_number']).first():
        return jsonify({'error': 'Registration number already exists'}), 400
    
    vehicle = Vehicle(
        brand=data['brand'],
        model=data['model'],
        year=data['year'],
        vin=data['vin'].upper(),
        reg_number=data['reg_number'].upper(),
        purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
        initial_mileage=data.get('initial_mileage', 0),
        vehicle_type=VehicleType[data['vehicle_type'].upper()],
        current_mileage=data.get('initial_mileage', 0)
    )
    
    db.session.add(vehicle)
    db.session.commit()
    
    return jsonify({'message': 'Vehicle created', 'vehicle': vehicle.to_dict()}), 201

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    """Обновление транспортного средства"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json()
    
    if 'vin' in data and data['vin'] != vehicle.vin:
        if not validate_vin(data['vin']):
            return jsonify({'error': 'Invalid VIN number'}), 400
        if Vehicle.query.filter_by(vin=data['vin']).first():
            return jsonify({'error': 'VIN already exists'}), 400
        vehicle.vin = data['vin'].upper()
    
    if 'reg_number' in data:
        vehicle.reg_number = data['reg_number'].upper()
    if 'brand' in data:
        vehicle.brand = data['brand']
    if 'model' in data:
        vehicle.model = data['model']
    if 'year' in data:
        vehicle.year = data['year']
    if 'current_mileage' in data:
        vehicle.current_mileage = data['current_mileage']
    if 'status' in data:
        vehicle.status = data['status']
    
    db.session.commit()
    return jsonify({'message': 'Vehicle updated', 'vehicle': vehicle.to_dict()}), 200

@api_bp.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    """Удаление транспортного средства"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    
    return jsonify({'message': 'Vehicle deleted'}), 200

# Maintenance API
@api_bp.route('/vehicles/<int:vehicle_id>/maintenance', methods=['GET'])
@jwt_required()
def get_maintenance(vehicle_id):
    """Получение истории ТО для транспортного средства"""
    maintenance = Maintenance.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(Maintenance.date.desc()).all()
    return jsonify([m.to_dict() for m in maintenance]), 200

@api_bp.route('/maintenance', methods=['POST'])
@jwt_required()
def create_maintenance():
    """Создание записи о ТО"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    vehicle = Vehicle.query.get_or_404(data['vehicle_id'])
    
    maintenance = Maintenance(
        vehicle_id=data['vehicle_id'],
        type=MaintenanceType[data['type'].upper()],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        mileage=data['mileage'],
        cost=data.get('cost', 0),
        description=data.get('description'),
        next_maintenance_km=data.get('next_maintenance_km', data['mileage'] + 10000)
    )
    
    # Обновляем текущий пробег ТС
    if data['mileage'] > vehicle.current_mileage:
        vehicle.current_mileage = data['mileage']
    
    db.session.add(maintenance)
    db.session.commit()
    
    return jsonify({'message': 'Maintenance created', 'maintenance': maintenance.to_dict()}), 201

@api_bp.route('/maintenance/<int:maintenance_id>', methods=['PUT'])
@jwt_required()
def update_maintenance(maintenance_id):
    """Обновление записи о ТО"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    data = request.get_json()
    
    if 'type' in data:
        maintenance.type = MaintenanceType[data['type'].upper()]
    if 'date' in data:
        maintenance.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'mileage' in data:
        maintenance.mileage = data['mileage']
        # Обновляем текущий пробег ТС, если новый пробег больше
        vehicle = Vehicle.query.get(maintenance.vehicle_id)
        if vehicle and data['mileage'] > vehicle.current_mileage:
            vehicle.current_mileage = data['mileage']
    if 'cost' in data:
        maintenance.cost = data['cost']
    if 'description' in data:
        maintenance.description = data.get('description')
    if 'next_maintenance_km' in data:
        maintenance.next_maintenance_km = data.get('next_maintenance_km')
    
    db.session.commit()
    return jsonify({'message': 'Maintenance updated', 'maintenance': maintenance.to_dict()}), 200

@api_bp.route('/maintenance/<int:maintenance_id>', methods=['DELETE'])
@jwt_required()
def delete_maintenance(maintenance_id):
    """Удаление записи о ТО"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    db.session.delete(maintenance)
    db.session.commit()
    
    return jsonify({'message': 'Maintenance deleted'}), 200

@api_bp.route('/maintenance/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_maintenance():
    """Получение предстоящих ТО"""
    vehicles = Vehicle.query.filter_by(status='active').all()
    upcoming = []
    
    for vehicle in vehicles:
        prediction = predict_next_maintenance(vehicle.id)
        if prediction:
            upcoming.append({
                'vehicle': vehicle.to_dict(),
                'prediction': prediction,
                'status': get_maintenance_status(vehicle.id)
            })
    
    # Сортируем по дате (predicted_date уже в формате ISO строки)
    upcoming.sort(key=lambda x: x['prediction']['predicted_date'])
    
    return jsonify(upcoming), 200

@api_bp.route('/maintenance/all', methods=['GET'])
@jwt_required()
def get_all_maintenance():
    """Получение всех записей ТО с информацией о ТС"""
    maintenance_records = Maintenance.query.order_by(Maintenance.date.desc()).all()
    result = []
    
    for m in maintenance_records:
        vehicle = Vehicle.query.get(m.vehicle_id)
        if vehicle:
            result.append({
                'id': m.id,
                'vehicle': vehicle.to_dict(),
                'type': m.type.value,
                'date': m.date.isoformat() if m.date else None,
                'mileage': m.mileage,
                'cost': float(m.cost) if m.cost else 0,
                'description': m.description,
                'next_maintenance_km': m.next_maintenance_km
            })
    
    return jsonify(result), 200

# Repairs API
@api_bp.route('/vehicles/<int:vehicle_id>/repairs', methods=['GET'])
@jwt_required()
def get_repairs(vehicle_id):
    """Получение истории ремонтов"""
    repairs = Repair.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(Repair.start_date.desc()).all()
    return jsonify([r.to_dict() for r in repairs]), 200

@api_bp.route('/repairs', methods=['POST'])
@jwt_required()
def create_repair():
    """Создание записи о ремонте"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MECHANIC]:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    vehicle = Vehicle.query.get_or_404(data['vehicle_id'])
    
    repair = Repair(
        vehicle_id=data['vehicle_id'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        description=data['description'],
        cost=data.get('cost', 0),
        status=RepairStatus[data.get('status', 'pending').upper()]
    )
    
    if repair.status == RepairStatus.IN_PROGRESS:
        vehicle.status = 'repair'
    
    db.session.add(repair)
    db.session.commit()
    
    # Отправка уведомления
    admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
    for admin in admin_users:
        send_repair_notification(admin.email, vehicle, repair)
    
    return jsonify({'message': 'Repair created', 'repair': repair.to_dict()}), 201

# Mileage API
@api_bp.route('/vehicles/<int:vehicle_id>/mileage', methods=['POST'])
@jwt_required()
def log_mileage(vehicle_id):
    """Запись пробега"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json()
    
    mileage_log = MileageLog(
        vehicle_id=vehicle_id,
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        mileage=data['mileage'],
        driver=data.get('driver'),
        notes=data.get('notes')
    )
    
    # Обновляем текущий пробег ТС
    if data['mileage'] > vehicle.current_mileage:
        vehicle.current_mileage = data['mileage']
    
    db.session.add(mileage_log)
    db.session.commit()
    
    return jsonify({'message': 'Mileage logged', 'log': mileage_log.to_dict()}), 201

@api_bp.route('/vehicles/<int:vehicle_id>/mileage', methods=['GET'])
@jwt_required()
def get_mileage_logs(vehicle_id):
    """Получение журнала пробега"""
    logs = MileageLog.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(MileageLog.date.desc()).all()
    return jsonify([l.to_dict() for l in logs]), 200

# Predictions API
@api_bp.route('/vehicles/<int:vehicle_id>/prediction', methods=['GET'])
@jwt_required()
def get_prediction(vehicle_id):
    """Получение прогноза следующего ТО"""
    prediction = predict_next_maintenance(vehicle_id)
    if not prediction:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    vehicle = Vehicle.query.get(vehicle_id)
    daily_mileage = calculate_daily_mileage(vehicle_id)
    
    return jsonify({
        'prediction': prediction,
        'daily_mileage': round(daily_mileage, 2),
        'status': get_maintenance_status(vehicle_id)
    }), 200


# ============ Web Routes ============

@web_bp.route('/')
def index():
    """Главная страница - редирект на календарь ТО"""
    return render_template('maintenance.html')

@web_bp.route('/vehicles')
def vehicles():
    """Страница реестра ТС"""
    return render_template('vehicles.html')

@web_bp.route('/vehicles/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    """Детальная страница ТС"""
    return render_template('vehicle_detail.html', vehicle_id=vehicle_id)

@web_bp.route('/maintenance')
def maintenance():
    """Календарь ТО"""
    return render_template('maintenance.html')

@web_bp.route('/predictions')
def predictions():
    """Прогнозы ТО"""
    return render_template('predictions.html')

@web_bp.route('/notifications')
def notifications():
    """Уведомления"""
    return render_template('notifications.html')

@web_bp.route('/login')
def login_page():
    """Страница входа"""
    return render_template('login.html')

