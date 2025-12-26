import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from datetime import date

def send_email(to_email, subject, body_html, body_text=None):
    """
    Отправка email через SMTP
    """
    try:
        smtp_host = current_app.config.get('SMTP_HOST')
        smtp_port = current_app.config.get('SMTP_PORT')
        smtp_user = current_app.config.get('SMTP_USER')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        
        if not all([smtp_host, smtp_user, smtp_password]):
            print(f"Email not configured. Would send to {to_email}: {subject}")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email
        
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_maintenance_notification(user_email, vehicle, maintenance_date, days_remaining):
    """
    Отправка уведомления о предстоящем ТО
    """
    subject = f"Напоминание: ТО для {vehicle.brand} {vehicle.model} ({vehicle.reg_number})"
    
    color = '#F39C12' if days_remaining > 7 else '#E74C3C'
    status_text = 'требуется в ближайшее время' if days_remaining <= 7 else 'приближается'
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #ECF0F1; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; padding: 30px; border-radius: 5px;">
            <h2 style="color: #2C3E50; margin-top: 0;">Уведомление о техническом обслуживании</h2>
            <p style="color: #2C3E50;">Техническое обслуживание {status_text} для следующего транспортного средства:</p>
            <div style="background-color: #ECF0F1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Марка/Модель:</strong> {vehicle.brand} {vehicle.model}</p>
                <p style="margin: 5px 0;"><strong>Гос. номер:</strong> {vehicle.reg_number}</p>
                <p style="margin: 5px 0;"><strong>VIN:</strong> {vehicle.vin}</p>
                <p style="margin: 5px 0;"><strong>Текущий пробег:</strong> {vehicle.current_mileage:,} км</p>
            </div>
            <div style="background-color: {color}; color: #FFFFFF; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0; font-size: 18px;"><strong>Дата ТО:</strong> {maintenance_date}</p>
                <p style="margin: 5px 0;"><strong>Осталось дней:</strong> {days_remaining}</p>
            </div>
            <p style="color: #7F8C8D; font-size: 12px; margin-top: 30px;">
                Это автоматическое уведомление от системы управления автопарком.
            </p>
        </div>
    </body>
    </html>
    """
    
    body_text = f"""
    Уведомление о техническом обслуживании
    
    Техническое обслуживание {status_text} для:
    Марка/Модель: {vehicle.brand} {vehicle.model}
    Гос. номер: {vehicle.reg_number}
    VIN: {vehicle.vin}
    Текущий пробег: {vehicle.current_mileage:,} км
    
    Дата ТО: {maintenance_date}
    Осталось дней: {days_remaining}
    """
    
    return send_email(user_email, subject, body_html, body_text)

def send_repair_notification(user_email, vehicle, repair):
    """
    Отправка уведомления о ремонте
    """
    subject = f"Ремонт: {vehicle.brand} {vehicle.model} ({vehicle.reg_number})"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #ECF0F1; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; padding: 30px; border-radius: 5px;">
            <h2 style="color: #E74C3C; margin-top: 0;">Уведомление о ремонте</h2>
            <div style="background-color: #ECF0F1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Марка/Модель:</strong> {vehicle.brand} {vehicle.model}</p>
                <p style="margin: 5px 0;"><strong>Гос. номер:</strong> {vehicle.reg_number}</p>
                <p style="margin: 5px 0;"><strong>Статус:</strong> {repair.status.value}</p>
                <p style="margin: 5px 0;"><strong>Дата начала:</strong> {repair.start_date}</p>
                {f'<p style="margin: 5px 0;"><strong>Дата окончания:</strong> {repair.end_date}</p>' if repair.end_date else ''}
                <p style="margin: 5px 0;"><strong>Стоимость:</strong> {repair.cost:,.2f} руб.</p>
            </div>
            <div style="background-color: #FFFFFF; border-left: 4px solid #E74C3C; padding: 15px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Описание:</strong></p>
                <p style="margin: 5px 0; color: #2C3E50;">{repair.description}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, body_html)


