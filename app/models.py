from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import enum

class UserRole(enum.Enum):
    ADMIN = 'admin'
    MECHANIC = 'mechanic'
    DRIVER = 'driver'

class VehicleType(enum.Enum):
    TRUCK = 'truck'
    CAR = 'car'
    SPECIAL = 'special'

class MaintenanceType(enum.Enum):
    REGULAR = 'regular'
    OIL_CHANGE = 'oil_change'
    TIRE_CHANGE = 'tire_change'
    BRAKE_SERVICE = 'brake_service'
    INSPECTION = 'inspection'
    OTHER = 'other'

class RepairStatus(enum.Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.DRIVER)
    full_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'full_name': self.full_name,
            'is_active': self.is_active
        }

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17), unique=True, nullable=False, index=True)
    reg_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    purchase_date = db.Column(db.Date, nullable=False)
    initial_mileage = db.Column(db.Integer, default=0)
    vehicle_type = db.Column(db.Enum(VehicleType), nullable=False)
    current_mileage = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, maintenance, repair, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_records = db.relationship('Maintenance', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    repairs = db.relationship('Repair', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    mileage_logs = db.relationship('MileageLog', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model,
            'year': self.year,
            'vin': self.vin,
            'reg_number': self.reg_number,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'initial_mileage': self.initial_mileage,
            'vehicle_type': self.vehicle_type.value,
            'current_mileage': self.current_mileage,
            'status': self.status
        }

class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    type = db.Column(db.Enum(MaintenanceType), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    mileage = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0)
    description = db.Column(db.Text)
    next_maintenance_km = db.Column(db.Integer)  # Expected mileage for next maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'type': self.type.value,
            'date': self.date.isoformat() if self.date else None,
            'mileage': self.mileage,
            'cost': float(self.cost) if self.cost else 0,
            'description': self.description,
            'next_maintenance_km': self.next_maintenance_km
        }

class Repair(db.Model):
    __tablename__ = 'repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.Enum(RepairStatus), nullable=False, default=RepairStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'cost': float(self.cost) if self.cost else 0,
            'status': self.status.value
        }

class MileageLog(db.Model):
    __tablename__ = 'mileage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    mileage = db.Column(db.Integer, nullable=False)
    driver = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'date': self.date.isoformat() if self.date else None,
            'mileage': self.mileage,
            'driver': self.driver,
            'notes': self.notes
        }

