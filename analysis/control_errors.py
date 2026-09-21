"""Errors shared by local API adapters and project operations."""


class ControlError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class BusyError(ControlError):
    def __init__(self):
        super().__init__('BUSY', '別の処理が実行中です。完了後に再試行してください。')


class ConflictError(ControlError):
    def __init__(self):
        super().__init__('CONFLICT', '解析結果または手修正が更新されています。再取得してから変更してください。')
