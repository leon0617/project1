from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.monitoring_result import MonitoringResult
from app.models.website import Website
from app.schemas.monitoring import SLAMetrics


class MonitoringService:
    @staticmethod
    def get_monitoring_results(
        db: Session,
        website_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[MonitoringResult], int]:
        query = db.query(MonitoringResult)
        
        if website_id:
            query = query.filter(MonitoringResult.website_id == website_id)
        if start_time:
            query = query.filter(MonitoringResult.timestamp >= start_time)
        if end_time:
            query = query.filter(MonitoringResult.timestamp <= end_time)
        
        total = query.count()
        results = query.order_by(MonitoringResult.timestamp.desc()).offset(skip).limit(limit).all()
        return results, total

    @staticmethod
    def get_sla_analytics(
        db: Session,
        website_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SLAMetrics]:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        query = db.query(
            Website.id,
            Website.name,
            func.count(MonitoringResult.id).label('total_checks'),
            func.sum(MonitoringResult.success).label('successful_checks'),
            func.avg(MonitoringResult.response_time).label('avg_response_time'),
        ).join(
            MonitoringResult, Website.id == MonitoringResult.website_id
        ).filter(
            MonitoringResult.timestamp >= start_date,
            MonitoringResult.timestamp <= end_date,
        )
        
        if website_id:
            query = query.filter(Website.id == website_id)
        
        query = query.group_by(Website.id, Website.name)
        
        results = query.all()
        
        sla_metrics = []
        for result in results:
            total_checks = result.total_checks or 0
            successful_checks = result.successful_checks or 0
            failed_checks = total_checks - successful_checks
            uptime_percentage = (successful_checks / total_checks * 100) if total_checks > 0 else 0.0
            
            sla_metrics.append(
                SLAMetrics(
                    website_id=result.id,
                    website_name=result.name,
                    uptime_percentage=uptime_percentage,
                    total_checks=total_checks,
                    successful_checks=successful_checks,
                    failed_checks=failed_checks,
                    average_response_time=result.avg_response_time,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        
        return sla_metrics
