"""
InvoiceFlow Pro - Analytics API Routes

Advanced analytics endpoints for business intelligence and reporting
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from app.core.deps import get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/dashboard")
async def get_dashboard_analytics(
    date_range: Optional[int] = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard analytics overview
    
    Returns KPIs, trends, and key metrics for the specified period
    """
    try:
        analytics_data = await analytics_service.get_dashboard_overview(
            user_id=current_user.id,
            date_range=date_range
        )
        
        return {
            "success": True,
            "data": analytics_data
        }
    except Exception as e:
        logger.error(f"Dashboard analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard analytics")


@router.get("/revenue")
async def get_revenue_analytics(
    period: str = Query("monthly", description="Time period: daily, weekly, monthly"),
    months: Optional[int] = Query(12, description="Number of months for monthly analysis", ge=1, le=36),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed revenue analytics with time-series data
    
    Supports daily, weekly, and monthly granularity
    """
    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Period must be daily, weekly, or monthly")
    
    try:
        revenue_data = await analytics_service.get_revenue_analytics(
            user_id=current_user.id,
            period=period,
            months=months
        )
        
        return {
            "success": True,
            "data": revenue_data
        }
    except Exception as e:
        logger.error(f"Revenue analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch revenue analytics")


@router.get("/customers")
async def get_customer_analytics(
    date_range: Optional[int] = Query(180, description="Number of days to analyze", ge=1, le=730),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive customer analytics
    
    Includes acquisition, retention, lifetime value, and behavior patterns
    """
    try:
        customer_data = await analytics_service.get_customer_analytics(
            user_id=current_user.id,
            date_range=date_range
        )
        
        return {
            "success": True,
            "data": customer_data
        }
    except Exception as e:
        logger.error(f"Customer analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer analytics")


@router.get("/performance")
async def get_performance_analytics(
    date_range: Optional[int] = Query(90, description="Number of days to analyze", ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get business performance analytics
    
    Includes efficiency metrics, cash flow analysis, and performance scoring
    """
    try:
        performance_data = await analytics_service.get_performance_analytics(
            user_id=current_user.id,
            date_range=date_range
        )
        
        return {
            "success": True,
            "data": performance_data
        }
    except Exception as e:
        logger.error(f"Performance analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance analytics")


@router.get("/export")
async def export_analytics_data(
    report_type: str = Query("dashboard", description="Type of report: dashboard, revenue, customers, performance"),
    format_type: str = Query("json", description="Export format: json, csv, pdf"),
    date_range: Optional[int] = Query(30, description="Number of days to include", ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Export analytics data in various formats
    
    Supports JSON, CSV, and PDF export formats
    """
    if report_type not in ["dashboard", "revenue", "customers", "performance"]:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    if format_type not in ["json", "csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be json, csv, or pdf")
    
    try:
        if report_type == "dashboard":
            data = await analytics_service.get_dashboard_overview(current_user.id, date_range)
        elif report_type == "revenue":
            data = await analytics_service.get_revenue_analytics(current_user.id)
        elif report_type == "customers":
            data = await analytics_service.get_customer_analytics(current_user.id, date_range)
        else:
            data = await analytics_service.get_performance_analytics(current_user.id, date_range)
        
        return {
            "success": True,
            "data": data,
            "export_info": {
                "format": format_type,
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": report_type
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics export error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export analytics data")