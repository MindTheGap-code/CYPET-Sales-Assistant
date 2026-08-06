from config import EXCLUDED_DOMAINS
from modules.outlook import OutlookReader
from modules.database import Database


class Scanner:

    def __init__(self):
        self.outlook = OutlookReader()
        self.database = Database()

    def scan(self, limit=100):

        messages = self.outlook.get_last_messages(limit)

        imported = 0
        skipped = 0

        for mail in messages:

            try:

                for recipient in mail.Recipients:

                    email = ""

                    try:

                        address = recipient.AddressEntry

                        if address.Type == "EX":

                            ex = address.GetExchangeUser()

                            if ex:
                                email = ex.PrimarySmtpAddress
                            else:
                                email = address.Address

                        else:
                            email = address.Address

                    except:
                        email = recipient.Address

                    domain = ""

                    if "@" in email:
                        domain = email.split("@")[1].lower()

                    # Esclude i domini interni
                    if domain in EXCLUDED_DOMAINS:
                        continue

                    if self.database.insert_email(
                        mail.EntryID,
                        str(mail.SentOn),
                        recipient.Name,
                        email,
                        domain,
                        mail.Subject
                    ):

                        imported += 1

                    else:

                        skipped += 1

            except Exception:
                pass

        return imported, skipped