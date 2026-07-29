from datetime import datetime, date
from app import db


class FamilyMember(db.Model):
    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    occupation = db.Column(db.String(100))
    is_emergency_contact = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref=db.backref('family_members', lazy='dynamic'))

    def __repr__(self):
        return f'<FamilyMember {self.name} ({self.relationship})>'


class MemberSkill(db.Model):
    __tablename__ = 'member_skills'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(30), default='Beginner')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref=db.backref('skills', lazy='dynamic'))

    def __repr__(self):
        return f'<MemberSkill {self.skill_name}>'


class MemberDocument(db.Model):
    __tablename__ = 'member_documents'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref=db.backref('documents', lazy='dynamic'))

    def __repr__(self):
        return f'<MemberDocument {self.document_type}: {self.file_name}>'


class BaptismRecord(db.Model):
    __tablename__ = 'baptism_records'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    baptism_date = db.Column(db.Date, nullable=False)
    baptized_by = db.Column(db.String(100))
    church_name = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref=db.backref('baptism_records', lazy='dynamic'))

    def __repr__(self):
        return f'<BaptismRecord {self.member_id} on {self.baptism_date}>'


class Giving(db.Model):
    __tablename__ = 'giving'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True)
    giver_name = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    giving_type = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), default='Cash')
    transaction_ref = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship('Member', backref=db.backref('givings', lazy='dynamic'))

    def __repr__(self):
        return f'<Giving {self.giving_type}: {self.amount}>'


class QRCodeAttendance(db.Model):
    __tablename__ = 'qr_attendance'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    member = db.relationship('Member', backref=db.backref('qr_attendances', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('member_id', 'date', 'service_type', name='uq_qr_member_date_service'),
    )

    def __repr__(self):
        return f'<QRCodeAttendance {self.member_id} - {self.service_type}>'


class ServiceSchedule(db.Model):
    __tablename__ = 'service_schedules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ServiceSchedule {self.name}>'
