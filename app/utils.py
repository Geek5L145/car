from datetime import datetime, timedelta, date
from app.models import Vehicle, Maintenance, MileageLog
from app import db
import re

def validate_vin(vin):
    """
    Валидация VIN-номера (17 символов, только буквы и цифры, исключая I, O, Q)
    """
    if not vin or len(vin) != 17:
        return False
    
    # VIN должен содержать только буквы и цифры, исключая I, O, Q
    pattern = r'^[A-HJ-NPR-Z0-9]{17}$'
    return bool(re.match(pattern, vin.upper()))

def calculate_daily_mileage(vehicle_id):
    """
    Расчет среднесуточного пробега на основе последних записей в журнале пробега
    """
    logs = MileageLog.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(MileageLog.date.desc()).limit(30).all()
    
    if len(logs) < 2:
        return 0
    
    # Сортируем по дате (старые сначала)
    logs_sorted = sorted(logs, key=lambda x: x.date)
    
    total_km = logs_sorted[-1].mileage - logs_sorted[0].mileage
    total_days = (logs_sorted[-1].date - logs_sorted[0].date).days
    
    if total_days == 0:
        return 0
    
    return total_km / total_days

def predict_next_maintenance(vehicle_id):
    """
    Прогнозирование даты следующего ТО на основе:
    - Последнего ТО
    - Текущего пробега
    - Среднесуточного пробега
    - Периодичности ТО (10000 км или 180 дней)
    """
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return None
    
    # Получаем последнее ТО
    last_maintenance = Maintenance.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(Maintenance.date.desc()).first()
    
    # Периодичность ТО
    maintenance_interval_km = 10000
    maintenance_interval_days = 180
    
    # Если есть последнее ТО с указанием следующего пробега
    if last_maintenance and last_maintenance.next_maintenance_km:
        target_mileage = last_maintenance.next_maintenance_km
    else:
        # Используем стандартную периодичность
        last_mileage = last_maintenance.mileage if last_maintenance else vehicle.initial_mileage
        target_mileage = last_mileage + maintenance_interval_km
    
    # Расчет по пробегу
    remaining_km = target_mileage - vehicle.current_mileage
    
    if remaining_km <= 0:
        # ТО уже просрочено
        return {
            'predicted_date': date.today().isoformat(),
            'predicted_mileage': vehicle.current_mileage,
            'is_overdue': True,
            'days_remaining': 0,
            'km_remaining': 0
        }
    
    # Рассчитываем среднесуточный пробег
    daily_mileage = calculate_daily_mileage(vehicle_id)
    
    if daily_mileage > 0:
        days_by_mileage = remaining_km / daily_mileage
    else:
        # Если нет данных о пробеге, используем только временной интервал
        days_by_mileage = maintenance_interval_days
    
    # Расчет по времени (от последнего ТО или от текущей даты)
    if last_maintenance:
        days_since_maintenance = (date.today() - last_maintenance.date).days
        days_by_time = maintenance_interval_days - days_since_maintenance
    else:
        days_by_time = maintenance_interval_days
    
    # Берем минимальное значение (что наступит раньше)
    days_remaining = min(days_by_mileage, days_by_time)
    
    predicted_date = date.today() + timedelta(days=int(days_remaining))
    
    return {
        'predicted_date': predicted_date.isoformat(),
        'predicted_mileage': target_mileage,
        'is_overdue': False,
        'days_remaining': int(days_remaining),
        'km_remaining': remaining_km
    }

def get_maintenance_status(vehicle_id):
    """
    Получение статуса ТО для транспортного средства
    """
    prediction = predict_next_maintenance(vehicle_id)
    
    if not prediction:
        return 'unknown'
    
    if prediction['is_overdue']:
        return 'overdue'
    
    days_remaining = prediction['days_remaining']
    
    if days_remaining <= 7:
        return 'urgent'
    elif days_remaining <= 30:
        return 'warning'
    else:
        return 'normal'

