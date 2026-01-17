from src.auth.require_session import require_session_token, NotAuthenticatedError

# security function
def showEvent(self, event):
    super().showEvent(event)
    try:
        require_session_token()
    except NotAuthenticatedError:
        self.back_requested.emit()  # oder stack.setCurrentWidget(StartPage)
