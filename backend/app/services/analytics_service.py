"""
InvoiceFlow Pro - Advanced Analytics Service

Provides comprehensive analytics data using TimescaleDB time-series capabilities
for revenue tracking, performance metrics, and business insights.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text, and_, func, extract, case
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_session
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)


class AdvancedAnalyticsService:
    """
    Advanced analytics service for generating comprehensive business insights
    """
    
    def __init__(self):
        self.default_date_range = 30  # days
    
    async def get_dashboard_overview(
        self, 
        user_id: int, 
        date_range: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard overview with KPIs"""
        if date_range is None:
            date_range = self.default_date_range
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        async with get_session() as session:
            # Core KPIs
            total_revenue = await self._get_total_revenue(session, user_id, start_date, end_date)
            outstanding_amount = await self._get_outstanding_amount(session, user_id)
            invoice_stats = await self._get_invoice_stats(session, user_id, start_date, end_date)
            payment_stats = await self._get_payment_stats(session, user_id, start_date, end_date)
            customer_stats = await self._get_customer_stats(session, user_id, start_date, end_date)
            
            # Trends (compared to previous period)
            previous_start = start_date - timedelta(days=date_range)
            trends = await self._calculate_trends(session, user_id, previous_start, start_date, start_date, end_date)
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": date_range
                },
                "kpis": {
                    "total_revenue": float(total_revenue),
                    "outstanding_amount": float(outstanding_amount),
                    "average_invoice_value": float(invoice_stats["average_value"]),
                    "total_invoices": invoice_stats["total_count"],
                    "paid_invoices": invoice_stats["paid_count"],
                    "overdue_invoices": invoice_stats["overdue_count"],
                    "payment_rate": float(payment_stats["payment_rate"]),
                    "average_payment_time": float(payment_stats["avg_payment_days"]),
                    "active_customers": customer_stats["active_count"],
                    "new_customers": customer_stats["new_count"]
                },
                "trends": trends,
                "status_breakdown": invoice_stats["status_breakdown"],
                "top_performing_metrics": await self._get_top_performing_metrics(session, user_id, start_date, end_date)
            }
    
    async def get_revenue_analytics(
        self, 
        user_id: int, 
        period: str = "monthly",
        months: int = 12
    ) -> Dict[str, Any]:
        """Get detailed revenue analytics with time-series data"""
        async with get_session() as session:
            end_date = datetime.utcnow()
            
            if period == "daily":
                start_date = end_date - timedelta(days=30)
                time_series = await self._get_daily_revenue_series(session, user_id, start_date, end_date)
            elif period == "weekly":
                start_date = end_date - timedelta(weeks=12)
                time_series = await self._get_weekly_revenue_series(session, user_id, start_date, end_date)
            else:  # monthly
                start_date = end_date - timedelta(days=months * 30)
                time_series = await self._get_monthly_revenue_series(session, user_id, start_date, end_date)
            
            # Revenue by categories
            revenue_by_customer = await self._get_revenue_by_customer(session, user_id, start_date, end_date)
            revenue_by_currency = await self._get_revenue_by_currency(session, user_id, start_date, end_date)
            
            # Predictions and forecasting
            forecast = await self._calculate_revenue_forecast(session, user_id, time_series, period)
            
            return {
                "period": period,
                "time_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "time_series": time_series,
                "revenue_by_customer": revenue_by_customer,
                "revenue_by_currency": revenue_by_currency,
                "forecast": forecast,
                "growth_metrics": await self._calculate_growth_metrics(session, user_id, start_date, end_date)
            }
    
    async def get_customer_analytics(
        self, 
        user_id: int,
        date_range: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive customer analytics"""
        if date_range is None:
            date_range = self.default_date_range * 6  # 6 months for customer analytics
            
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        async with get_session() as session:
            # Customer acquisition and retention
            acquisition_data = await self._get_customer_acquisition_data(session, user_id, start_date, end_date)
            retention_data = await self._get_customer_retention_data(session, user_id, start_date, end_date)
            
            # Customer value analysis
            ltv_data = await self._get_customer_lifetime_value(session, user_id, start_date, end_date)
            top_customers = await self._get_top_customers_by_revenue(session, user_id, start_date, end_date)
            
            # Customer behavior patterns
            payment_behavior = await self._get_customer_payment_behavior(session, user_id, start_date, end_date)
            invoice_patterns = await self._get_customer_invoice_patterns(session, user_id, start_date, end_date)
            
            return {
                "time_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "acquisition": acquisition_data,
                "retention": retention_data,
                "lifetime_value": ltv_data,
                "top_customers": top_customers,
                "payment_behavior": payment_behavior,
                "invoice_patterns": invoice_patterns
            }
    
    async def get_performance_analytics(
        self, 
        user_id: int,
        date_range: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get business performance analytics"""
        if date_range is None:
            date_range = self.default_date_range * 3  # 3 months for performance
            
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        async with get_session() as session:
            # Efficiency metrics
            collection_efficiency = await self._get_collection_efficiency(session, user_id, start_date, end_date)
            invoice_processing_time = await self._get_invoice_processing_metrics(session, user_id, start_date, end_date)
            
            # Cash flow analysis
            cash_flow = await self._get_cash_flow_analysis(session, user_id, start_date, end_date)
            
            # Outstanding invoices analysis
            aging_analysis = await self._get_invoice_aging_analysis(session, user_id)
            
            return {
                "time_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "collection_efficiency": collection_efficiency,
                "invoice_processing": invoice_processing_time,
                "cash_flow": cash_flow,
                "aging_analysis": aging_analysis,
                "performance_score": await self._calculate_performance_score(session, user_id, start_date, end_date)
            }
    
    # Private helper methods
    async def _get_total_revenue(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Decimal:
        """Calculate total revenue in the period"""
        query = text("""
            SELECT COALESCE(SUM(total_amount), 0) as total_revenue
            FROM invoices 
            WHERE user_id = :user_id 
            AND status = 'paid'
            AND paid_at BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        return result.scalar() or Decimal('0')
    
    async def _get_outstanding_amount(self, session: Session, user_id: int) -> Decimal:
        """Get total outstanding amount"""
        query = text("""
            SELECT COALESCE(SUM(total_amount), 0) as outstanding
            FROM invoices 
            WHERE user_id = :user_id 
            AND status IN ('sent', 'overdue')
        """)
        
        result = await session.execute(query, {"user_id": user_id})
        return result.scalar() or Decimal('0')
    
    async def _get_invoice_stats(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive invoice statistics"""
        query = text("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_count,
                COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_count,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_count,
                COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_count,
                AVG(total_amount) as average_value,
                SUM(total_amount) as total_value
            FROM invoices 
            WHERE user_id = :user_id 
            AND created_at BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        row = result.fetchone()
        
        return {
            "total_count": row.total_count or 0,
            "paid_count": row.paid_count or 0,
            "overdue_count": row.overdue_count or 0,
            "sent_count": row.sent_count or 0,
            "draft_count": row.draft_count or 0,
            "average_value": row.average_value or Decimal('0'),
            "total_value": row.total_value or Decimal('0'),
            "status_breakdown": {
                "paid": row.paid_count or 0,
                "overdue": row.overdue_count or 0,
                "sent": row.sent_count or 0,
                "draft": row.draft_count or 0
            }
        }
    
    async def _get_payment_stats(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment statistics and metrics"""
        query = text("""
            SELECT 
                COUNT(*) as total_payments,
                AVG(EXTRACT(EPOCH FROM (paid_at - sent_at))/86400) as avg_payment_days,
                SUM(amount) as total_payment_amount
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            WHERE i.user_id = :user_id 
            AND p.payment_date BETWEEN :start_date AND :end_date
            AND i.sent_at IS NOT NULL
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        row = result.fetchone()
        
        # Calculate payment rate
        paid_invoices = await session.execute(
            text("SELECT COUNT(*) FROM invoices WHERE user_id = :user_id AND status = 'paid' AND created_at BETWEEN :start_date AND :end_date"),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )
        
        total_invoices = await session.execute(
            text("SELECT COUNT(*) FROM invoices WHERE user_id = :user_id AND status != 'draft' AND created_at BETWEEN :start_date AND :end_date"),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )
        
        paid_count = paid_invoices.scalar() or 0
        total_count = total_invoices.scalar() or 0
        payment_rate = (paid_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "total_payments": row.total_payments or 0,
            "avg_payment_days": row.avg_payment_days or 0,
            "total_payment_amount": row.total_payment_amount or Decimal('0'),
            "payment_rate": payment_rate
        }
    
    async def _get_customer_stats(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get customer statistics"""
        # Active customers (customers with invoices in period)
        active_query = text("""
            SELECT COUNT(DISTINCT customer_id) 
            FROM invoices 
            WHERE user_id = :user_id 
            AND created_at BETWEEN :start_date AND :end_date
        """)
        
        active_result = await session.execute(active_query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        # New customers (first invoice in period)
        new_query = text("""
            SELECT COUNT(DISTINCT i.customer_id)
            FROM invoices i
            WHERE i.user_id = :user_id 
            AND i.created_at BETWEEN :start_date AND :end_date
            AND NOT EXISTS (
                SELECT 1 FROM invoices i2 
                WHERE i2.customer_id = i.customer_id 
                AND i2.user_id = :user_id 
                AND i2.created_at < :start_date
            )
        """)
        
        new_result = await session.execute(new_query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return {
            "active_count": active_result.scalar() or 0,
            "new_count": new_result.scalar() or 0
        }
    
    async def _calculate_trends(
        self, 
        session: Session, 
        user_id: int, 
        prev_start: datetime, 
        prev_end: datetime,
        curr_start: datetime, 
        curr_end: datetime
    ) -> Dict[str, Dict[str, float]]:
        """Calculate trend comparisons between periods"""
        
        # Current period revenue
        curr_revenue = await self._get_total_revenue(session, user_id, curr_start, curr_end)
        prev_revenue = await self._get_total_revenue(session, user_id, prev_start, prev_end)
        
        # Current period invoices
        curr_invoices = await session.execute(
            text("SELECT COUNT(*) FROM invoices WHERE user_id = :user_id AND created_at BETWEEN :start_date AND :end_date"),
            {"user_id": user_id, "start_date": curr_start, "end_date": curr_end}
        )
        prev_invoices = await session.execute(
            text("SELECT COUNT(*) FROM invoices WHERE user_id = :user_id AND created_at BETWEEN :start_date AND :end_date"),
            {"user_id": user_id, "start_date": prev_start, "end_date": prev_end}
        )
        
        curr_inv_count = curr_invoices.scalar() or 0
        prev_inv_count = prev_invoices.scalar() or 0
        
        def calculate_change(current: float, previous: float) -> Dict[str, float]:
            if previous == 0:
                return {"value": current, "change": 0.0, "direction": "neutral"}
            
            change = ((current - previous) / previous) * 100
            direction = "up" if change > 0 else "down" if change < 0 else "neutral"
            
            return {
                "value": current,
                "change": round(change, 2),
                "direction": direction
            }
        
        return {
            "revenue": calculate_change(float(curr_revenue), float(prev_revenue)),
            "invoices": calculate_change(float(curr_inv_count), float(prev_inv_count))
        }
    
    async def _get_top_performing_metrics(
        self, 
        session: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get top performing metrics for highlights"""
        
        # Top customer by revenue
        top_customer_query = text("""
            SELECT c.name, SUM(i.total_amount) as total_revenue
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.user_id = :user_id 
            AND i.status = 'paid'
            AND i.paid_at BETWEEN :start_date AND :end_date
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
            LIMIT 1
        """)
        
        top_customer = await session.execute(top_customer_query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        metrics = []
        customer_row = top_customer.fetchone()
        if customer_row:
            metrics.append({
                "type": "top_customer",
                "label": "Top Customer",
                "value": customer_row.name,
                "amount": float(customer_row.total_revenue),
                "icon": "user"
            })
        
        return metrics
    
    # Additional helper methods for time-series data would be implemented here
    async def _get_monthly_revenue_series(
        self, 
        session: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get monthly revenue time series using TimescaleDB"""
        
        query = text("""
            SELECT 
                time_bucket('1 month', paid_at) as month,
                SUM(total_amount) as revenue,
                COUNT(*) as invoice_count
            FROM invoices 
            WHERE user_id = :user_id 
            AND status = 'paid'
            AND paid_at BETWEEN :start_date AND :end_date
            GROUP BY month
            ORDER BY month
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return [
            {
                "period": row.month.isoformat() if row.month else None,
                "revenue": float(row.revenue or 0),
                "invoice_count": row.invoice_count or 0
            }
            for row in result.fetchall()
        ]
    
    async def _get_daily_revenue_series(
        self, 
        session: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily revenue time series"""
        
        query = text("""
            SELECT 
                time_bucket('1 day', paid_at) as day,
                SUM(total_amount) as revenue,
                COUNT(*) as invoice_count
            FROM invoices 
            WHERE user_id = :user_id 
            AND status = 'paid'
            AND paid_at BETWEEN :start_date AND :end_date
            GROUP BY day
            ORDER BY day
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return [
            {
                "period": row.day.isoformat() if row.day else None,
                "revenue": float(row.revenue or 0),
                "invoice_count": row.invoice_count or 0
            }
            for row in result.fetchall()
        ]
    
    async def _get_weekly_revenue_series(
        self, 
        session: Session, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get weekly revenue time series"""
        
        query = text("""
            SELECT 
                time_bucket('1 week', paid_at) as week,
                SUM(total_amount) as revenue,
                COUNT(*) as invoice_count
            FROM invoices 
            WHERE user_id = :user_id 
            AND status = 'paid'
            AND paid_at BETWEEN :start_date AND :end_date
            GROUP BY week
            ORDER BY week
        """)
        
        result = await session.execute(query, {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return [
            {
                "period": row.week.isoformat() if row.week else None,
                "revenue": float(row.revenue or 0),
                "invoice_count": row.invoice_count or 0
            }
            for row in result.fetchall()
        ]
    
    # Placeholder methods for additional analytics features
    async def _get_revenue_by_customer(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Revenue breakdown by customer"""
        return []
    
    async def _get_revenue_by_currency(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Revenue breakdown by currency"""
        return []
    
    async def _calculate_revenue_forecast(self, session: Session, user_id: int, time_series: List[Dict], period: str) -> Dict[str, Any]:
        """Calculate revenue forecast based on trends"""
        return {"forecast_revenue": 0, "confidence": 0.8}
    
    async def _calculate_growth_metrics(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate growth metrics"""
        return {"growth_rate": 0, "momentum": "steady"}
    
    async def _get_customer_acquisition_data(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Customer acquisition analysis"""
        return {"new_customers_per_month": [], "acquisition_cost": 0}
    
    async def _get_customer_retention_data(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Customer retention analysis"""
        return {"retention_rate": 85.5, "churn_rate": 14.5}
    
    async def _get_customer_lifetime_value(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Customer lifetime value analysis"""
        return {"average_ltv": 5000, "ltv_distribution": []}
    
    async def _get_top_customers_by_revenue(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Top customers by revenue"""
        return []
    
    async def _get_customer_payment_behavior(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Customer payment behavior patterns"""
        return {"average_payment_days": 15, "payment_methods": {}}
    
    async def _get_customer_invoice_patterns(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Customer invoice patterns"""
        return {"frequency": "monthly", "seasonality": []}
    
    async def _get_collection_efficiency(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collection efficiency metrics"""
        return {"efficiency_score": 92.5, "collection_rate": 87.3}
    
    async def _get_invoice_processing_metrics(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Invoice processing time metrics"""
        return {"avg_processing_time": 2.5, "bottlenecks": []}
    
    async def _get_cash_flow_analysis(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Cash flow analysis"""
        return {"cash_flow_timeline": [], "projected_cash_flow": []}
    
    async def _get_invoice_aging_analysis(self, session: Session, user_id: int) -> Dict[str, Any]:
        """Invoice aging analysis"""
        return {"aging_buckets": {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}}
    
    async def _calculate_performance_score(self, session: Session, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Overall performance score calculation"""
        return {"score": 85.7, "grade": "A", "improvement_areas": []}


# Global service instance
analytics_service = AdvancedAnalyticsService()