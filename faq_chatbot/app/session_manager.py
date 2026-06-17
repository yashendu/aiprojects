import uuid


class SessionManager:
    def __init__(self):
        self._sessions = {}

    def create(self):
        sid = uuid.uuid4().hex[:12]
        self._sessions[sid] = {
            'history': [],
            'document_loaded': False,
            'document_name': '',
        }
        return sid

    def get(self, sid):
        return self._sessions.get(sid)

    def add_message(self, sid, role, text):
        sess = self._sessions.get(sid)
        if sess:
            sess['history'].append({'role': role, 'text': text})

    def get_history(self, sid):
        sess = self._sessions.get(sid)
        return sess['history'] if sess else []

    def set_document(self, sid, name):
        sess = self._sessions.get(sid)
        if sess:
            sess['document_loaded'] = True
            sess['document_name'] = name

    def clear(self, sid):
        if sid in self._sessions:
            del self._sessions[sid]


sessions = SessionManager()
