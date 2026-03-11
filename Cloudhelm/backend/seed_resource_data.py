"""
Seed Resource Efficiency data from Loop_ResourceDashboard.
This script populates the database with the exact data from Loop_ResourceDashboard dump.
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.append('.')

from backend.core.db import SessionLocal
from backend.models.resource import Resource, ResourceMetric, Recommendation


def seed_loop_data():
    """Seed database with exact data from Loop_ResourceDashboard."""
    db: Session = SessionLocal()
    
    try:
        print("🧹 Clearing existing resource data...")
        db.query(ResourceMetric).delete()
        db.query(Recommendation).delete()
        db.query(Resource).delete()
        db.commit()
        print("✅ Cleared existing data")
        
        # Create resources - exact data from Loop_ResourceDashboard dump
        print("\n📦 Creating resources...")
        resources = [
            Resource(
                id="vm-1",
                name="app-server-prod-02",
                resource_type="EC2",
                team="Backend",
                environment="production",
                waste_score=12.5
            ),
            Resource(
                id="vm-2",
                name="cache-node-staging",
                resource_type="EC2",
                team="Platform",
                environment="staging",
                waste_score=45.0
            ),
            Resource(
                id="vm-3",
                name="web-server-dev-01",
                resource_type="EC2",
                team="Frontend",
                environment="development",
                waste_score=78.2
            ),
            Resource(
                id="vm-4",
                name="db-replica-prod",
                resource_type="RDS",
                team="Backend",
                environment="production",
                waste_score=5.0
            ),
            Resource(
                id="vm-5",
                name="analytics-worker-01",
                resource_type="EC2",
                team="Data",
                environment="production",
                waste_score=32.1
            ),
            Resource(
                id="vm-6",
                name="temp-build-agent",
                resource_type="EC2",
                team="DevOps",
                environment="development",
                waste_score=92.5
            ),
        ]
        
        db.add_all(resources)
        db.commit()
        print(f"✅ Created {len(resources)} resources")
        
        # Create recommendations - exact data from Loop_ResourceDashboard dump
        print("\n💡 Creating recommendations...")
        recommendations = [
            Recommendation(
                resource_id="vm-2",
                recommendation_type="rightsizing",
                description="Memory usage consistently below 40%.",
                potential_savings=120.0,
                suggested_action="Downgrade to t3.medium",
                confidence=0.85
            ),
            Recommendation(
                resource_id="vm-3",
                recommendation_type="schedule",
                description="Development server running 24/7.",
                potential_savings=85.0,
                suggested_action="Shutdown 8 PM - 8 AM",
                confidence=0.90
            ),
            Recommendation(
                resource_id="vm-5",
                recommendation_type="rightsizing",
                description="Over-provisioned IOPS.",
                potential_savings=45.0,
                suggested_action="Switch to gp3",
                confidence=0.80
            ),
            Recommendation(
                resource_id="vm-6",
                recommendation_type="schedule",
                description="Idle build agent.",
                potential_savings=200.0,
                suggested_action="Terminate when idle",
                confidence=0.95
            ),
        ]
        
        db.add_all(recommendations)
        db.commit()
        print(f"✅ Created {len(recommendations)} recommendations")
        
        # Generate realistic metrics for the past 7 days
        print("\n📊 Generating resource metrics (7 days)...")
        now = datetime.utcnow()
        metrics_created = 0
        
        # Metrics configuration based on waste scores
        metrics_config = {
            "vm-1": {"cpu": 65.0, "memory": 70.0, "disk": 80.0, "network": 60.0},  # Low waste
            "vm-2": {"cpu": 35.0, "memory": 38.0, "disk": 45.0, "network": 30.0},  # Medium waste
            "vm-3": {"cpu": 15.0, "memory": 18.0, "disk": 25.0, "network": 12.0},  # High waste
            "vm-4": {"cpu": 75.0, "memory": 80.0, "disk": 85.0, "network": 70.0},  # Very low waste
            "vm-5": {"cpu": 45.0, "memory": 50.0, "disk": 55.0, "network": 40.0},  # Medium waste
            "vm-6": {"cpu": 8.0, "memory": 10.0, "disk": 15.0, "network": 5.0},    # Very high waste
        }
        
        for resource in resources:
            config = metrics_config[resource.id]
            
            # Create metrics every 4 hours for 7 days (42 data points per resource)
            for day in range(7):
                for hour in [0, 4, 8, 12, 16, 20]:
                    timestamp = now - timedelta(days=day, hours=hour)
                    
                    # Add some variance to make it realistic
                    import random
                    variance = random.uniform(-5, 5)
                    
                    metric = ResourceMetric(
                        resource_id=resource.id,
                        timestamp=timestamp,
                        cpu_utilization=max(5.0, min(95.0, config["cpu"] + variance)),
                        memory_utilization=max(5.0, min(95.0, config["memory"] + variance)),
                        disk_io=max(10.0, min(200.0, config["disk"] + variance * 2)),
                        network_io=max(5.0, min(150.0, config["network"] + variance * 1.5))
                    )
                    db.add(metric)
                    metrics_created += 1
        
        db.commit()
        print(f"✅ Created {metrics_created} metrics")
        
        # Summary
        print("\n" + "="*60)
        print("🎉 SEED COMPLETE!")
        print("="*60)
        print(f"Resources:        {len(resources)}")
        print(f"Recommendations:  {len(recommendations)}")
        print(f"Metrics:          {metrics_created}")
        print("\nTeams: Backend, Platform, Frontend, Data, DevOps")
        print("Environments: production, staging, development")
        print("\n✅ Data is now visible in Resource Efficiency page!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Starting Resource Efficiency data seed...")
    print("📍 Source: Loop_ResourceDashboard database dump")
    print()
    seed_loop_data()
