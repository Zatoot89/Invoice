from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app.blueprints.client import client_bp
from app.forms import ClientForm
from app import db
from app.models import Client

@client_bp.route('/clients')
@login_required
def list_clients():
    clients = Client.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('client/list.html', clients=clients, title='Clients')

@client_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            address=form.address.data,
            organization_id=current_user.organization_id
        )
        db.session.add(client)
        db.session.commit()
        flash('Client has been added successfully.')
        return redirect(url_for('client.list_clients'))
    return render_template('client/add.html', form=form, title='Add Client')
