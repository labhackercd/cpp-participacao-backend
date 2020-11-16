from participacao.celery import app
from .scrappy import get_rooms
from .models import RoomAnalysisAudiencias
import datetime


@app.task(name="task1")
def task_get_rooms():
    rooms = get_rooms('all')
    batch_size = 100

    def create_room(room):
        data = {
            "title_reunion": room["title_reunion"],
            "online_users": room["online_users"],
            "legislative_body": room["legislative_body"],
            "legislative_body_initials": room["legislative_body_initials"],
            "questions_count": room["questions_count"],
            "answered_questions_count": room["answered_questions_count"],
            "messages_count": room["messages_count"],
            "votes_count": room["votes_count"],
            "participants_count": room["participants_count"],
        }
        if room['id'] == '':
            room_id = None
        else:
            room_id = room['id']
        if room['cod_reunion'] == '':
            meeting_code = None
        else:
            meeting_code = room['cod_reunion']
        date = datetime.datetime.strptime(room['date'], '%Y-%m-%dT%H:%M:%S')

        room_object = RoomAnalysisAudiencias(data=data, room_id=room_id,
                                             start_date=date.date(),
                                             end_date=date.date(),
                                             meeting_code=meeting_code)

        return room_object

    room_alaysis = [create_room(room) for room in rooms]

    RoomAnalysisAudiencias.objects.bulk_create(room_alaysis, batch_size)
