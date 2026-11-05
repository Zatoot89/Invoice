"""
InvoiceFlow Pro - Customer Service
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.customer import Customer
from app.core.exceptions import ResourceNotFoundException, ValidationException


class CustomerService:
    """
    Service class for customer operations
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by primary ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    async def get_by_email(self, user_id: int, email: str) -> Optional[Customer]:
        """Get customer by email for a user"""
        return (
            self.db.query(Customer)
            .filter(Customer.user_id == user_id, Customer.email == email)
            .first()
        )

    async def get_customers(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Customer], int]:
        """Get paginated list of customers for a user"""
        query = self.db.query(Customer).filter(Customer.user_id == user_id)

        if is_active is not None:
            query = query.filter(Customer.is_active == is_active)

        if search:
            query = query.filter(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.email.ilike(f"%{search}%"),
                    Customer.company.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        customers = (
            query.order_by(desc(Customer.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return customers, total

    async def create_customer(
        self,
        user_id: int,
        name: str,
        email: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        address_line_1: Optional[str] = None,
        address_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        tax_number: Optional[str] = None,
        notes: Optional[str] = None,
        preferred_currency: str = "USD",
        payment_terms: int = 30,
    ) -> Customer:
        """Create a new customer"""
        customer = Customer(
            user_id=user_id,
            name=name,
            email=email,
            company=company,
            phone=phone,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            tax_number=tax_number,
            notes=notes,
            preferred_currency=preferred_currency,
            payment_terms=payment_terms,
            is_active=True,
        )

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    async def update_customer(
        self,
        customer_id: int,
        user_id: int,
        update_data: Dict[str, Any],
    ) -> Customer:
        """Update existing customer details"""
        customer = (
            self.db.query(Customer)
            .filter(Customer.id == customer_id, Customer.user_id == user_id)
            .first()
        )
        if not customer:
            raise ResourceNotFoundException("Customer", customer_id)

        for key, value in update_data.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)

        self.db.commit()
        self.db.refresh(customer)
        return customer

    async def delete_customer(self, customer_id: int, user_id: int) -> bool:
        """Delete customer or mark inactive"""
        customer = (
            self.db.query(Customer)
            .filter(Customer.id == customer_id, Customer.user_id == user_id)
            .first()
        )
        if not customer:
            raise ResourceNotFoundException("Customer", customer_id)

        self.db.delete(customer)
        self.db.commit()
        return True
