import win32com.client


class OutlookReader:

    def __init__(self):

        self.outlook = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook.GetNamespace("MAPI")
        self.sent = self.namespace.GetDefaultFolder(5)

    def get_last_messages(self, number=10):

        items = self.sent.Items
        items.Sort("[SentOn]", True)

        result = []

        count = 0

        for mail in items:

            if count >= number:
                break

            try:

                if mail.Class != 43:
                    continue

                result.append(mail)

                count += 1

            except:
                pass

        return result