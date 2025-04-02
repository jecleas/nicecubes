class IceTrayHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ice_tray_id = db.Column(db.Integer, db.ForeignKey('ice_tray.id'), nullable=False)
    is_frozen = db.Column(db.Boolean, default=False)
    frozen_at = db.Column(db.DateTime)
    ice_tray = db.relationship('IceTray', backref='history')

