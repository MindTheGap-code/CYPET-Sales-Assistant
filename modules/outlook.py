import win32com.client


class OutlookReader:
    SENT_FOLDER = 5
    MAIL_ITEM_CLASS = 43

    def __init__(self):
        self.outlook = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook.GetNamespace("MAPI")
        self.sent = self.namespace.GetDefaultFolder(self.SENT_FOLDER)

    def get_last_messages(self, number=10):
        items = self.sent.Items
        items.Sort("[SentOn]", True)

        result = []

        for mail in items:
            if len(result) >= number:
                break

            try:
                if mail.Class != self.MAIL_ITEM_CLASS:
                    continue

                result.append(mail)

            except Exception:
                continue

        return result

    def close(self):
        self.outlook = None
        self.namespace = None
        self.sent = None
