"""Settings API for GDial.

This module provides API endpoints for managing system settings.
"""
import uuid
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlmodel import Session

from .database import get_session
from .models.settings import (
    SystemSetting, 
    DtmfSetting, 
    SmsSettings, 
    NotificationSettings,
    SecuritySettings
)
from .schemas.settings import (
    SystemSettingResponse,
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingBulkUpdate,
    DtmfSettingResponse,
    DtmfSettingUpdate,
    SmsSettingsResponse,
    SmsSettingsUpdate,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    SecuritySettingsResponse,
    SecuritySettingsUpdate,
    SettingsGroup
)
from .settings import (
    get_dtmf_settings,
    get_sms_settings, 
    get_notification_settings,
    get_security_settings,
    get_settings_by_group
)

router = APIRouter(prefix="/settings", tags=["settings"])

# System Settings Routes
@router.get("/system", response_model=List[SystemSettingResponse])
def get_all_system_settings(session: Session = Depends(get_session)):
    """Get all system settings."""
    return session.query(SystemSetting).all()

@router.get("/system/{key}", response_model=SystemSettingResponse)
def get_system_setting(key: str, session: Session = Depends(get_session)):
    """Get a system setting by key."""
    setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting with key '{key}' not found")
    return setting

@router.post("/system", response_model=SystemSettingResponse)
def create_system_setting(setting: SystemSettingCreate, session: Session = Depends(get_session)):
    """Create a new system setting."""
    existing = session.query(SystemSetting).filter(SystemSetting.key == setting.key).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Setting with key '{setting.key}' already exists")
    
    new_setting = SystemSetting(
        key=setting.key,
        value=setting.value,
        value_type=setting.value_type,
        description=setting.description,
        group=setting.group
    )
    session.add(new_setting)
    session.commit()
    session.refresh(new_setting)
    return new_setting

@router.put("/system/{key}", response_model=SystemSettingResponse)
def update_system_setting(
    key: str, 
    setting: SystemSettingUpdate, 
    session: Session = Depends(get_session)
):
    """Update a system setting."""
    db_setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail=f"Setting with key '{key}' not found")
    
    update_data = setting.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)
    
    session.add(db_setting)
    session.commit()
    session.refresh(db_setting)
    return db_setting

@router.delete("/system/{key}", response_model=SystemSettingResponse)
def delete_system_setting(key: str, session: Session = Depends(get_session)):
    """Delete a system setting."""
    setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting with key '{key}' not found")
    
    session.delete(setting)
    session.commit()
    return setting

@router.put("/system", response_model=Dict[str, str])
def bulk_update_system_settings(update: SystemSettingBulkUpdate, session: Session = Depends(get_session)):
    """Bulk update system settings."""
    result = {}
    for key, value in update.settings.items():
        setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            # Get the current value type
            value_type = setting.value_type
            
            # Use set_value to properly handle type conversion
            SystemSetting.set_value(
                session=session,
                key=key,
                value=value,
                value_type=value_type,
                description=setting.description,
                group=setting.group
            )
            result[key] = "updated"
        else:
            result[key] = "not_found"
    
    return result

@router.get("/system/groups", response_model=List[SettingsGroup])
def get_settings_groups(group: Optional[str] = None, session: Session = Depends(get_session)):
    """Get settings organized by group."""
    settings_by_group = get_settings_by_group(session, group)
    result = []
    
    for group_name, settings in settings_by_group.items():
        result.append(SettingsGroup(
            group_name=group_name,
            settings=settings
        ))
        
    return result

# DTMF Settings Routes
@router.get("/dtmf", response_model=DtmfSettingResponse)
def get_dtmf_settings_api(session: Session = Depends(get_session)):
    """Get DTMF settings."""
    return get_dtmf_settings(session)

@router.put("/dtmf", response_model=DtmfSettingResponse)
def update_dtmf_settings(
    settings: DtmfSettingUpdate, 
    session: Session = Depends(get_session)
):
    """Update DTMF settings."""
    db_settings = get_dtmf_settings(session)
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings

# SMS Settings Routes
@router.get("/sms", response_model=SmsSettingsResponse)
def get_sms_settings_api(session: Session = Depends(get_session)):
    """Get SMS settings."""
    return get_sms_settings(session)

@router.put("/sms", response_model=SmsSettingsResponse)
def update_sms_settings(
    settings: SmsSettingsUpdate, 
    session: Session = Depends(get_session)
):
    """Update SMS settings."""
    db_settings = get_sms_settings(session)
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings

# Notification Settings Routes
@router.get("/notifications", response_model=NotificationSettingsResponse)
def get_notification_settings_api(session: Session = Depends(get_session)):
    """Get notification settings."""
    return get_notification_settings(session)

@router.put("/notifications", response_model=NotificationSettingsResponse)
def update_notification_settings(
    settings: NotificationSettingsUpdate, 
    session: Session = Depends(get_session)
):
    """Update notification settings."""
    db_settings = get_notification_settings(session)
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings

# Security Settings Routes
@router.get("/security", response_model=SecuritySettingsResponse)
def get_security_settings_api(session: Session = Depends(get_session)):
    """Get security settings."""
    return get_security_settings(session)

@router.put("/security", response_model=SecuritySettingsResponse)
def update_security_settings(
    settings: SecuritySettingsUpdate, 
    session: Session = Depends(get_session)
):
    """Update security settings."""
    db_settings = get_security_settings(session)
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings