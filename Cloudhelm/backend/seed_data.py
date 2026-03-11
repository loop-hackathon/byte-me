"""
Seed script to populate the database with sample data for testing.
This will make the Overview page load much faster.
"""
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import sessionmaker
from backend.core.db import engine
from backend.models.cost import CostAggregate, CostAnomaly, Budget, Incident, Deployment

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_sample_data():
    """Generate sample data for the last 90 days"""
    session = SessionLocal()
    
    try:
        print("🌱 Seeding database with sample data...")
        
        # Clear existing data
        print("  Clearing existing data...")
        session.query(CostAggregate).delete()
        session.query(CostAnomaly).delete()
        session.query(Budget).delete()
        session.query(Incident).delete()
        session.query(Deployment).delete()
        session.commit()
        
        # Generate data for last 90 days
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        clouds = ['AWS', 'Azure', 'GCP']
        teams = ['Frontend', 'Backend', 'DevOps', 'Data', 'ML', 'Security', 'Mobile']
        services = ['web-app', 'api-gateway', 'database', 'cache', 'storage', 'compute', 'monitoring']
        regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        environments = ['prod', 'staging', 'dev']
        
        # 1. Generate Cost Aggregates (daily costs)
        print("  Generating cost aggregates...")
        cost_records = []
        current_date = start_date
        
        while current_date <= end_date:
            for cloud in clouds:
                for team in teams:
                    for service in services[:3]:  # Limit services to keep data manageable
                        for env in environments:
                            # Generate realistic cost with some variation
                            base_cost = random.uniform(50, 500)
                            if env == 'prod':
                                base_cost *= 3  # Production costs more
                            elif env == 'staging':
                                base_cost *= 1.5
                            
                            # Add some weekly and monthly patterns
                            day_of_week = current_date.weekday()
                            if day_of_week >= 5:  # Weekend
                                base_cost *= 0.7
                            
                            cost_records.append(CostAggregate(
                                ts_date=current_date,
                                cloud=cloud,
                                team=team,
                                service=service,
                                region=random.choice(regions),
                                env=env,
                                total_cost=Decimal(str(round(base_cost, 2)))
                            ))
            
            current_date += timedelta(days=1)
        
        session.bulk_save_objects(cost_records)
        print(f"    Created {len(cost_records)} cost records")
        
        # 2. Generate Cost Anomalies
        print("  Generating cost anomalies...")
        anomaly_records = []
        
        # Generate 20-30 anomalies over the period
        for _ in range(25):
            anomaly_date = start_date + timedelta(days=random.randint(0, 89))
            team = random.choice(teams)
            service = random.choice(services)
            cloud = random.choice(clouds)
            
            expected_cost = random.uniform(100, 800)
            # Create anomaly (either spike or drop)
            if random.choice([True, False]):
                # Spike
                actual_cost = expected_cost * random.uniform(1.5, 3.0)
                direction = 'up'
                severity = random.choice(['medium', 'high'])
            else:
                # Drop
                actual_cost = expected_cost * random.uniform(0.3, 0.8)
                direction = 'down'
                severity = random.choice(['low', 'medium'])
            
            anomaly_records.append(CostAnomaly(
                ts_date=anomaly_date,
                cloud=cloud,
                team=team,
                service=service,
                region=random.choice(regions),
                env=random.choice(environments),
                actual_cost=Decimal(str(round(actual_cost, 2))),
                expected_cost=Decimal(str(round(expected_cost, 2))),
                anomaly_score=random.uniform(0.7, 0.95),
                direction=direction,
                severity=severity
            ))
        
        session.bulk_save_objects(anomaly_records)
        print(f"    Created {len(anomaly_records)} anomaly records")
        
        # 3. Generate Budgets
        print("  Generating budgets...")
        budget_records = []
        
        for team in teams:
            # Each team has a monthly budget
            budget_amount = random.uniform(5000, 25000)
            budget_records.append(Budget(
                team=team,
                service=None,  # Team-level budget
                monthly_budget_amount=Decimal(str(round(budget_amount, 2))),
                currency='USD'
            ))
        
        session.bulk_save_objects(budget_records)
        print(f"    Created {len(budget_records)} budget records")
        
        # 4. Generate Incidents
        print("  Generating incidents...")
        incident_records = []
        
        # Generate 15-20 incidents over the period
        for i in range(18):
            incident_date = start_date + timedelta(days=random.randint(0, 89))
            status = random.choice(['open', 'investigating', 'resolved'])
            severity = random.choice(['low', 'medium', 'high', 'critical'])
            
            # Some incidents are resolved
            resolved_date = None
            if status == 'resolved' or random.choice([True, False]):
                resolved_date = incident_date + timedelta(hours=random.randint(1, 48))
                status = 'resolved'
            
            incident_records.append(Incident(
                title=f"Service outage in {random.choice(services)} - {random.choice(['Database connection', 'High latency', 'Memory leak', 'API timeout', 'SSL certificate'])}",
                status=status,
                severity=severity,
                created_at=incident_date,
                resolved_at=resolved_date,
                service=random.choice(services),
                team=random.choice(teams),
                env=random.choice(environments)
            ))
        
        session.bulk_save_objects(incident_records)
        print(f"    Created {len(incident_records)} incident records")
        
        # 5. Generate Deployments
        print("  Generating deployments...")
        deployment_records = []
        
        # Generate deployments for last 30 days (more recent activity)
        deployment_start = end_date - timedelta(days=30)
        current_date = deployment_start
        
        while current_date <= end_date:
            # 2-5 deployments per day
            daily_deployments = random.randint(2, 5)
            
            for _ in range(daily_deployments):
                status = random.choice(['success', 'success', 'success', 'failed'])  # 75% success rate
                
                deployment_records.append(Deployment(
                    service=random.choice(services),
                    environment=random.choice(environments),
                    status=status,
                    deployed_at=current_date,
                    deployed_by=random.choice(['alice', 'bob', 'charlie', 'diana', 'eve']),
                    version=f"v{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 10)}",
                    commit_sha=f"{random.randint(100000, 999999):x}"
                ))
            
            current_date += timedelta(days=1)
        
        session.bulk_save_objects(deployment_records)
        print(f"    Created {len(deployment_records)} deployment records")
        
        # Commit all changes
        session.commit()
        print("✅ Database seeded successfully!")
        
        # Print summary
        print("\n📊 Data Summary:")
        print(f"  Cost Aggregates: {session.query(CostAggregate).count()}")
        print(f"  Cost Anomalies: {session.query(CostAnomaly).count()}")
        print(f"  Budgets: {session.query(Budget).count()}")
        print(f"  Incidents: {session.query(Incident).count()}")
        print(f"  Deployments: {session.query(Deployment).count()}")
        
        # Show some sample KPIs
        total_cost = session.query(CostAggregate).filter(
            CostAggregate.ts_date >= end_date - timedelta(days=30)
        ).with_entities(CostAggregate.total_cost).all()
        
        if total_cost:
            monthly_spend = sum(cost[0] for cost in total_cost)
            print(f"\n💰 Sample KPIs:")
            print(f"  Total 30-day spend: ${monthly_spend:,.2f}")
            print(f"  Active anomalies: {session.query(CostAnomaly).filter(CostAnomaly.ts_date >= end_date - timedelta(days=7)).count()}")
            print(f"  Open incidents: {session.query(Incident).filter(Incident.status.in_(['open', 'investigating'])).count()}")
            print(f"  Recent deployments: {session.query(Deployment).filter(Deployment.deployed_at >= end_date - timedelta(days=7)).count()}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    generate_sample_data()