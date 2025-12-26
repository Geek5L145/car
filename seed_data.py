"""
Скрипт для наполнения базы данных тестовыми данными
"""
from app import create_app, db
from app.models import User, Vehicle, Maintenance, Repair, MileageLog, UserRole, VehicleType, MaintenanceType, RepairStatus
from datetime import datetime, date, timedelta
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        # Очистка базы данных
        print("Очистка базы данных...")
        db.drop_all()
        db.create_all()
        
        # Создание пользователей
        print("Создание пользователей...")
        users = [
            User(
                username='admin',
                email='admin@fleet.local',
                role=UserRole.ADMIN,
                full_name='Администратор системы'
            ),
            User(
                username='mechanic1',
                email='mechanic1@fleet.local',
                role=UserRole.MECHANIC,
                full_name='Иванов Иван Иванович'
            ),
            User(
                username='driver1',
                email='driver1@fleet.local',
                role=UserRole.DRIVER,
                full_name='Петров Петр Петрович'
            ),
            User(
                username='driver2',
                email='driver2@fleet.local',
                role=UserRole.DRIVER,
                full_name='Сидоров Сидор Сидорович'
            )
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        
        db.session.commit()
        print(f"Создано {len(users)} пользователей")
        
        # Создание транспортных средств
        print("Создание транспортных средств...")
        brands_models = [
            ('КАМАЗ', '65117', VehicleType.TRUCK),
            ('КАМАЗ', '43118', VehicleType.TRUCK),
            ('МАЗ', '6312', VehicleType.TRUCK),
            ('ГАЗ', '3309', VehicleType.TRUCK),
            ('Урал', '4320', VehicleType.TRUCK),
            ('Lada', 'Granta', VehicleType.CAR),
            ('Lada', 'Vesta', VehicleType.CAR),
            ('Lada', 'XRAY', VehicleType.CAR),
            ('УАЗ', 'Patriot', VehicleType.CAR),
            ('ГАЗ', 'Газель', VehicleType.CAR),
            ('JCB', '3CX', VehicleType.SPECIAL),
            ('Caterpillar', '320D', VehicleType.SPECIAL),
            ('Komatsu', 'PC200', VehicleType.SPECIAL),
            ('БелАЗ', '7555', VehicleType.SPECIAL),
            ('МТЗ', '82', VehicleType.SPECIAL)
        ]
        
        vehicles = []
        vin_chars = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789'
        
        for i, (brand, model, v_type) in enumerate(brands_models):
            # Генерация VIN (17 символов)
            vin = ''.join(random.choices(vin_chars, k=17))
            
            # Генерация гос. номера
            reg_number = f"{random.choice(['А', 'В', 'Е', 'К', 'М', 'Н', 'О', 'Р', 'С', 'Т', 'У', 'Х'])}{random.randint(100, 999)}{random.choice(['А', 'В', 'Е', 'К', 'М', 'Н', 'О', 'Р', 'С', 'Т', 'У', 'Х'])}{random.choice(['А', 'В', 'Е', 'К', 'М', 'Н', 'О', 'Р', 'С', 'Т', 'У', 'Х'])}{random.randint(1, 199)}"
            
            purchase_date = date.today() - timedelta(days=random.randint(365, 2000))
            initial_mileage = random.randint(0, 50000)
            current_mileage = initial_mileage + random.randint(10000, 150000)
            
            vehicle = Vehicle(
                brand=brand,
                model=model,
                year=random.randint(2015, 2023),
                vin=vin,
                reg_number=reg_number,
                purchase_date=purchase_date,
                initial_mileage=initial_mileage,
                vehicle_type=v_type,
                current_mileage=current_mileage,
                status='active' if random.random() > 0.2 else 'repair'
            )
            
            vehicles.append(vehicle)
            db.session.add(vehicle)
        
        db.session.commit()
        print(f"Создано {len(vehicles)} транспортных средств")
        
        # Создание журнала пробега
        print("Создание журнала пробега...")
        mileage_logs_count = 0
        for vehicle in vehicles:
            # Создаем записи о пробеге за последние 2 года
            start_date = date.today() - timedelta(days=730)
            current_mileage = vehicle.initial_mileage
            daily_increment = random.randint(50, 300)
            
            for day in range(0, 730, random.randint(1, 7)):  # Запись каждые 1-7 дней
                log_date = start_date + timedelta(days=day)
                if log_date > date.today():
                    break
                
                current_mileage += daily_increment * random.randint(1, 7)
                
                mileage_log = MileageLog(
                    vehicle_id=vehicle.id,
                    date=log_date,
                    mileage=current_mileage,
                    driver=random.choice(['Петров П.П.', 'Сидоров С.С.', 'Иванов И.И.']),
                    notes=f"Запись пробега за {log_date.strftime('%d.%m.%Y')}"
                )
                
                db.session.add(mileage_log)
                mileage_logs_count += 1
        
        db.session.commit()
        print(f"Создано {mileage_logs_count} записей в журнале пробега")
        
        # Создание истории ТО за последние 2 года
        print("Создание истории ТО...")
        maintenance_count = 0
        maintenance_types = [
            MaintenanceType.REGULAR,
            MaintenanceType.OIL_CHANGE,
            MaintenanceType.TIRE_CHANGE,
            MaintenanceType.BRAKE_SERVICE,
            MaintenanceType.INSPECTION
        ]
        
        for vehicle in vehicles:
            # Создаем 3-6 записей о ТО за последние 2 года
            num_maintenances = random.randint(3, 6)
            last_mileage = vehicle.initial_mileage
            
            for i in range(num_maintenances):
                maintenance_date = date.today() - timedelta(days=random.randint(30, 730))
                last_mileage += random.randint(8000, 15000)
                
                maintenance = Maintenance(
                    vehicle_id=vehicle.id,
                    type=random.choice(maintenance_types),
                    date=maintenance_date,
                    mileage=last_mileage,
                    cost=random.randint(5000, 50000),
                    description=f"Техническое обслуживание: {random.choice(['Замена масла', 'Проверка систем', 'Замена фильтров', 'Диагностика', 'Регулировка'])}",
                    next_maintenance_km=last_mileage + 10000
                )
                
                db.session.add(maintenance)
                maintenance_count += 1
        
        db.session.commit()
        print(f"Создано {maintenance_count} записей о ТО")
        
        # Создание ремонтов (3-5 активных)
        print("Создание ремонтов...")
        repair_count = 0
        repair_statuses = [RepairStatus.PENDING, RepairStatus.IN_PROGRESS, RepairStatus.COMPLETED]
        repair_descriptions = [
            'Ремонт двигателя',
            'Замена коробки передач',
            'Ремонт подвески',
            'Покраска кузова',
            'Ремонт электроники',
            'Замена тормозной системы',
            'Ремонт системы охлаждения'
        ]
        
        # Активные ремонты
        vehicles_in_repair = [v for v in vehicles if v.status == 'repair'][:5]
        for vehicle in vehicles_in_repair:
            start_date = date.today() - timedelta(days=random.randint(1, 30))
            end_date = None if random.random() > 0.3 else start_date + timedelta(days=random.randint(1, 15))
            status = RepairStatus.IN_PROGRESS if not end_date else RepairStatus.COMPLETED
            
            repair = Repair(
                vehicle_id=vehicle.id,
                start_date=start_date,
                end_date=end_date,
                description=random.choice(repair_descriptions),
                cost=random.randint(10000, 200000) if end_date else 0,
                status=status
            )
            
            db.session.add(repair)
            repair_count += 1
        
        # Завершенные ремонты
        for vehicle in random.sample(vehicles, min(10, len(vehicles))):
            if vehicle.status != 'repair':
                start_date = date.today() - timedelta(days=random.randint(60, 365))
                end_date = start_date + timedelta(days=random.randint(1, 20))
                
                repair = Repair(
                    vehicle_id=vehicle.id,
                    start_date=start_date,
                    end_date=end_date,
                    description=random.choice(repair_descriptions),
                    cost=random.randint(10000, 200000),
                    status=RepairStatus.COMPLETED
                )
                
                db.session.add(repair)
                repair_count += 1
        
        db.session.commit()
        print(f"Создано {repair_count} записей о ремонтах")
        
        print("\n✅ База данных успешно заполнена тестовыми данными!")
        print("\nДанные для входа:")
        print("  Администратор: admin / password123")
        print("  Механик: mechanic1 / password123")
        print("  Водитель: driver1 / password123")

if __name__ == '__main__':
    seed_database()


