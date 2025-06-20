from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    appointment_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in Rupiah
    payment_method = db.Column(db.String(50), nullable=False)  # transfer, cash, credit_card
    payment_reference = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Payment {self.payment_reference}>'