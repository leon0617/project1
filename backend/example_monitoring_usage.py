"""
Example script demonstrating the website monitoring system.

This script shows how to:
1. Set up the database
2. Create websites to monitor
3. Run manual checks
4. View monitoring results

Run this script with:
    python example_monitoring_usage.py
"""

import asyncio
from datetime import datetime, timezone
from app.core.database import SessionLocal, engine, Base
from app.models import Website, MonitorCheck, DowntimeWindow
from app.services.monitoring import monitoring_service


async def main():
    print("=== Website Monitoring Example ===\n")
    
    # Create tables
    print("1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✓ Tables created\n")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Create some test websites
        print("2. Creating test websites...")
        
        website1 = Website(
            url="https://www.google.com",
            name="Google",
            enabled=True,
            check_interval=300,
        )
        
        website2 = Website(
            url="https://www.github.com",
            name="GitHub",
            enabled=True,
            check_interval=300,
        )
        
        website3 = Website(
            url="https://this-does-not-exist-12345.com",
            name="Non-existent Site",
            enabled=True,
            check_interval=300,
        )
        
        db.add_all([website1, website2, website3])
        db.commit()
        db.refresh(website1)
        db.refresh(website2)
        db.refresh(website3)
        
        print(f"   ✓ Created website: {website1.name} ({website1.url})")
        print(f"   ✓ Created website: {website2.name} ({website2.url})")
        print(f"   ✓ Created website: {website3.name} ({website3.url})")
        print()
        
        # Perform checks on all websites
        print("3. Performing monitoring checks...")
        print()
        
        for website in [website1, website2, website3]:
            print(f"   Checking {website.name}...")
            check = await monitoring_service.perform_check(db, website)
            
            if check.is_available:
                print(f"   ✓ {website.name} is UP")
                print(f"     Status: {check.status_code}")
                print(f"     Response time: {check.response_time:.3f}s")
            else:
                print(f"   ✗ {website.name} is DOWN")
                print(f"     Error: {check.error_message}")
            print()
        
        # Display monitoring results
        print("4. Monitoring Results Summary:")
        print()
        
        all_websites = db.query(Website).all()
        for website in all_websites:
            checks = db.query(MonitorCheck).filter_by(website_id=website.id).all()
            downtime_windows = db.query(DowntimeWindow).filter_by(website_id=website.id).all()
            
            print(f"   {website.name}:")
            print(f"   - URL: {website.url}")
            print(f"   - Total Checks: {len(checks)}")
            print(f"   - Downtime Windows: {len(downtime_windows)}")
            
            if checks:
                latest_check = checks[-1]
                print(f"   - Latest Status: {'UP' if latest_check.is_available else 'DOWN'}")
                if latest_check.response_time:
                    print(f"   - Latest Response Time: {latest_check.response_time:.3f}s")
            
            if downtime_windows:
                for window in downtime_windows:
                    if window.end_time:
                        duration = (window.end_time - window.start_time).total_seconds()
                        print(f"   - Downtime: {duration:.1f}s (from {window.start_time})")
                    else:
                        print(f"   - Currently Down (since {window.start_time})")
            
            print()
        
        print("5. Example complete!")
        print()
        print("To start the API server with automatic monitoring:")
        print("   uvicorn app.main:app --reload")
        print()
        print("Then create websites via API:")
        print('   curl -X POST http://localhost:8000/api/websites \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"url": "https://example.com", "name": "Example", "enabled": true, "check_interval": 300}\'')
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
