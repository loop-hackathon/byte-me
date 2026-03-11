"""
Cost ingestion services for AWS, GCP, and Azure cost exports.
"""
import pandas as pd
import io
from datetime import datetime, date
from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.models.cost import CloudCost
from backend.schemas.cost import UploadResponse


async def ingest_aws_cost_csv(file: UploadFile, db: Session, user_id: int) -> UploadResponse:
    """
    Ingest AWS Cost and Usage Report (CUR) CSV file.
    
    Supports two modes:
    1. Standard AWS CUR format with specific column names
    2. Flexible format - auto-detects service/cost/date columns by keyword
    
    Args:
        file: Uploaded CSV file
        db: Database session
        user_id: Current user ID
        
    Returns:
        UploadResponse with ingestion statistics
    """
    try:
        # Read file contents
        contents = await file.read()
        content_str = contents.decode('utf-8')
        
        # Use pandas for flexible parsing
        df = pd.read_csv(io.StringIO(content_str))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty CSV file")
        
        available_columns = df.columns.tolist()
        
        # --- FLEXIBLE COLUMN DETECTION ---
        # Try standard AWS CUR mapping first, then fall back to auto-detection
        aws_column_mapping = {
            'lineItem/UsageStartDate': 'usage_date',
            'lineItem/UnblendedCost': 'cost',
            'lineItem/UsageAccountId': 'account_id',
            'product/region': 'region',
            'lineItem/ProductCode': 'service',
            'lineItem/UsageType': 'usage_type',
            'lineItem/CurrencyCode': 'currency',
            'resourceTags/user:env': 'env',
            'resourceTags/user:team': 'team',
        }
        
        column_map = {}
        for aws_col, norm_col in aws_column_mapping.items():
            for col in available_columns:
                if col == aws_col or col.lower() == aws_col.lower():
                    column_map[norm_col] = col
                    break
        
        # Check if standard format has required columns
        required = ['usage_date', 'cost', 'service']
        missing = [c for c in required if c not in column_map]
        
        if missing:
            # Fall back to flexible auto-detection (feature_2-style)
            column_map = {}
            
            # Auto-detect service column
            service_col = next(
                (c for c in available_columns
                 if 'service' in c.lower() or 'product' in c.lower()),
                available_columns[0]
            )
            column_map['service'] = service_col
            
            # Auto-detect cost column
            cost_col = next(
                (c for c in available_columns
                 if 'cost' in c.lower() or 'amount' in c.lower()),
                available_columns[-1]
            )
            column_map['cost'] = cost_col
            
            # Auto-detect date column
            date_col = next(
                (c for c in available_columns
                 if 'date' in c.lower() or 'time' in c.lower()),
                None
            )
            if date_col:
                column_map['usage_date'] = date_col
            
            # Auto-detect region / availability zone
            region_col = next(
                (c for c in available_columns
                 if 'region' in c.lower() or 'zone' in c.lower()
                 or 'availability' in c.lower() or 'location' in c.lower()),
                None
            )
            if region_col:
                column_map['region'] = region_col
            
            # Auto-detect usage type
            usage_col = next(
                (c for c in available_columns
                 if 'usage' in c.lower() and 'type' in c.lower()),
                None
            )
            if usage_col:
                column_map['usage_type'] = usage_col
            
            # Auto-detect currency
            currency_col = next(
                (c for c in available_columns
                 if 'currency' in c.lower()),
                None
            )
            if currency_col:
                column_map['currency'] = currency_col
            
            # Auto-detect account
            account_col = next(
                (c for c in available_columns
                 if 'account' in c.lower() or 'subscription' in c.lower()
                 or 'project' in c.lower()),
                None
            )
            if account_col:
                column_map['account_id'] = account_col
        
        # Ensure cost is numeric
        cost_col_name = column_map.get('cost', column_map.get('cost'))
        if cost_col_name:
            df[cost_col_name] = pd.to_numeric(df[cost_col_name], errors='coerce').fillna(0)
        
        # Handle date parsing
        if 'usage_date' in column_map:
            date_col_name = column_map['usage_date']
            df[date_col_name] = pd.to_datetime(
                df[date_col_name], errors='coerce', dayfirst=True
            )
        
        # Process rows
        records = []
        total_cost = 0.0
        dates = []
        
        for _, row in df.iterrows():
            try:
                # Parse cost
                cost_val = float(row[column_map['cost']]) if 'cost' in column_map else 0.0
                if cost_val <= 0:
                    continue
                
                # Parse date
                if 'usage_date' in column_map:
                    dt = row[column_map['usage_date']]
                    if pd.isna(dt):
                        usage_date = date.today()
                    else:
                        usage_date = dt.date() if hasattr(dt, 'date') else date.today()
                else:
                    usage_date = date.today()
                
                # Extract service
                service = str(row[column_map['service']]) if 'service' in column_map else 'unknown'
                
                # Extract region
                region = str(row[column_map['region']]) if 'region' in column_map and pd.notna(row.get(column_map.get('region', ''), None)) else 'unknown'
                
                # Extract account
                account_id = str(row[column_map['account_id']]) if 'account_id' in column_map and pd.notna(row.get(column_map.get('account_id', ''), None)) else 'default'
                
                # Extract optional fields
                usage_type = str(row[column_map['usage_type']]) if 'usage_type' in column_map and pd.notna(row.get(column_map.get('usage_type', ''), None)) else None
                currency = str(row[column_map['currency']]) if 'currency' in column_map and pd.notna(row.get(column_map.get('currency', ''), None)) else 'USD'
                env = str(row[column_map['env']]) if 'env' in column_map and pd.notna(row.get(column_map.get('env', ''), None)) else None
                team = str(row[column_map['team']]) if 'team' in column_map and pd.notna(row.get(column_map.get('team', ''), None)) else None
                
                record = CloudCost(
                    ts_date=usage_date,
                    cloud='aws',
                    account_id=account_id,
                    service=service,
                    region=region,
                    env=env,
                    team=team,
                    usage_type=usage_type,
                    cost_amount=cost_val,
                    currency=currency,
                    user_id=user_id,
                )
                records.append(record)
                total_cost += cost_val
                dates.append(usage_date)
                
            except (ValueError, TypeError):
                continue
        
        if not records:
            raise HTTPException(status_code=400, detail="No valid cost records found in CSV")
        
        # Bulk insert in batches
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.bulk_save_objects(batch)
            db.commit()
        
        # Calculate statistics
        start_date = min(dates) if dates else date.today()
        end_date = max(dates) if dates else date.today()
        rows_ingested = len(records)
        
        return UploadResponse(
            rows_ingested=rows_ingested,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            cloud='aws'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing AWS CUR: {str(e)}")


async def ingest_gcp_cost_file(file: UploadFile, db: Session, user_id: int) -> UploadResponse:
    """
    Ingest GCP billing export file (CSV or JSON).
    
    Args:
        file: Uploaded file
        db: Database session
        
    Returns:
        UploadResponse with ingestion statistics
    """
    try:
        # Read file contents
        contents = await file.read()
        
        # Try CSV first, then JSON
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except:
            df = pd.read_json(io.BytesIO(contents))
        
        # GCP billing export column mapping
        # Common columns:
        # - usage_start_time
        # - cost
        # - project.id
        # - service.description
        # - location.region
        # - labels.env
        # - labels.team
        
        column_mapping = {
            'usage_start_time': 'usage_date',
            'cost': 'cost',
            'project.id': 'account_id',
            'service.description': 'service',
            'location.region': 'region',
            'sku.description': 'usage_type',
            'currency': 'currency',
            'labels.env': 'env',
            'labels.team': 'team',
        }
        
        # Map columns
        available_columns = df.columns.tolist()
        mapped_data = {}
        
        for gcp_col, normalized_col in column_mapping.items():
            matching_col = None
            for col in available_columns:
                if col == gcp_col or col.lower() == gcp_col.lower():
                    matching_col = col
                    break
            
            if matching_col:
                mapped_data[normalized_col] = df[matching_col]
        
        normalized_df = pd.DataFrame(mapped_data)
        
        # Ensure required columns
        required_cols = ['usage_date', 'cost', 'account_id', 'service']
        missing_cols = [col for col in required_cols if col not in normalized_df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in GCP export: {missing_cols}"
            )
        
        # Convert date
        normalized_df['usage_date'] = pd.to_datetime(normalized_df['usage_date']).dt.date
        
        # Fill missing columns
        if 'region' not in normalized_df.columns:
            normalized_df['region'] = 'global'
        if 'env' not in normalized_df.columns:
            normalized_df['env'] = None
        if 'team' not in normalized_df.columns:
            normalized_df['team'] = None
        if 'usage_type' not in normalized_df.columns:
            normalized_df['usage_type'] = None
        if 'currency' not in normalized_df.columns:
            normalized_df['currency'] = 'USD'
        
        # Filter zero-cost rows
        normalized_df = normalized_df[normalized_df['cost'] > 0]
        
        # Prepare records
        records = []
        for _, row in normalized_df.iterrows():
            record = CloudCost(
                ts_date=row['usage_date'],
                cloud='gcp',
                account_id=str(row['account_id']),
                service=str(row['service']),
                region=str(row['region']),
                env=str(row['env']) if pd.notna(row['env']) else None,
                team=str(row['team']) if pd.notna(row['team']) else None,
                usage_type=str(row['usage_type']) if pd.notna(row['usage_type']) else None,
                cost_amount=float(row['cost']),
                currency=str(row['currency']),
                user_id=user_id
            )
            records.append(record)
        
        # Bulk insert
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.bulk_save_objects(batch)
            db.commit()
        
        # Statistics
        start_date = normalized_df['usage_date'].min()
        end_date = normalized_df['usage_date'].max()
        total_cost = float(normalized_df['cost'].sum())
        rows_ingested = len(records)
        
        return UploadResponse(
            rows_ingested=rows_ingested,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            cloud='gcp'
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing GCP export: {str(e)}")


async def ingest_azure_cost_csv(file: UploadFile, db: Session, user_id: int) -> UploadResponse:
    """
    Ingest Azure cost export CSV file.
    
    Args:
        file: Uploaded CSV file
        db: Database session
        
    Returns:
        UploadResponse with ingestion statistics
    """
    try:
        # Read file contents
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Azure cost export column mapping
        # Common columns:
        # - Date
        # - Cost
        # - SubscriptionId
        # - ServiceName
        # - ResourceLocation
        # - MeterCategory
        # - Tags (JSON string with env, team)
        
        column_mapping = {
            'Date': 'usage_date',
            'UsageDate': 'usage_date',
            'Cost': 'cost',
            'CostInBillingCurrency': 'cost',
            'SubscriptionId': 'account_id',
            'SubscriptionGuid': 'account_id',
            'ServiceName': 'service',
            'ConsumedService': 'service',
            'ResourceLocation': 'region',
            'Location': 'region',
            'MeterCategory': 'usage_type',
            'BillingCurrency': 'currency',
        }
        
        # Map columns
        available_columns = df.columns.tolist()
        mapped_data = {}
        
        for azure_col, normalized_col in column_mapping.items():
            matching_col = None
            for col in available_columns:
                if col == azure_col or col.lower() == azure_col.lower():
                    matching_col = col
                    break
            
            if matching_col:
                mapped_data[normalized_col] = df[matching_col]
        
        normalized_df = pd.DataFrame(mapped_data)
        
        # Ensure required columns
        required_cols = ['usage_date', 'cost', 'account_id', 'service']
        missing_cols = [col for col in required_cols if col not in normalized_df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in Azure export: {missing_cols}"
            )
        
        # Convert date
        normalized_df['usage_date'] = pd.to_datetime(normalized_df['usage_date']).dt.date
        
        # Fill missing columns
        if 'region' not in normalized_df.columns:
            normalized_df['region'] = 'unknown'
        if 'usage_type' not in normalized_df.columns:
            normalized_df['usage_type'] = None
        if 'currency' not in normalized_df.columns:
            normalized_df['currency'] = 'USD'
        
        # Parse tags if available (Azure stores tags as JSON string)
        normalized_df['env'] = None
        normalized_df['team'] = None
        
        if 'Tags' in df.columns:
            import json
            for idx, tags_str in df['Tags'].items():
                if pd.notna(tags_str) and tags_str:
                    try:
                        tags = json.loads(tags_str)
                        if 'env' in tags:
                            normalized_df.at[idx, 'env'] = tags['env']
                        if 'team' in tags:
                            normalized_df.at[idx, 'team'] = tags['team']
                    except:
                        pass
        
        # Filter zero-cost rows
        normalized_df = normalized_df[normalized_df['cost'] > 0]
        
        # Prepare records
        records = []
        for _, row in normalized_df.iterrows():
            record = CloudCost(
                ts_date=row['usage_date'],
                cloud='azure',
                account_id=str(row['account_id']),
                service=str(row['service']),
                region=str(row['region']),
                env=str(row['env']) if pd.notna(row['env']) else None,
                team=str(row['team']) if pd.notna(row['team']) else None,
                usage_type=str(row['usage_type']) if pd.notna(row['usage_type']) else None,
                cost_amount=float(row['cost']),
                currency=str(row['currency']),
                user_id=user_id
            )
            records.append(record)
        
        # Bulk insert
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.bulk_save_objects(batch)
            db.commit()
        
        # Statistics
        start_date = normalized_df['usage_date'].min()
        end_date = normalized_df['usage_date'].max()
        total_cost = float(normalized_df['cost'].sum())
        rows_ingested = len(records)
        
        return UploadResponse(
            rows_ingested=rows_ingested,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            cloud='azure'
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing Azure export: {str(e)}")
