from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.core import events as events_core
from app.core.auth_mongo import get_current_user

router = APIRouter()


@router.get('/events', response_model=list[EventOut])
def list_events(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    lst = events_core.list_events(str(user_id))
    return [EventOut(**e) for e in lst]


@router.get('/events/{event_id}', response_model=EventOut)
def get_event(event_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    e = events_core.get_event(str(user_id), event_id)
    if not e:
        raise HTTPException(status_code=404, detail='Not found')
    return EventOut(**e)


@router.put('/events/{event_id}', response_model=EventOut)
def update_event(event_id: str, payload: EventUpdate, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    e = events_core.update_event(str(user_id), event_id, payload.model_dump(exclude_unset=True))
    if not e:
        raise HTTPException(status_code=404, detail='Not found')
    return EventOut(**e)


@router.delete('/events/{event_id}', status_code=204)
def delete_event(event_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    ok = events_core.delete_event(str(user_id), event_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Not found')
    return
