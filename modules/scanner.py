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
                    email = self._get_recipient_email(recipient)

                    if not email:
                        skipped += 1
                        continue

                    domain = self._get_domain(email)

                    if domain in EXCLUDED_DOMAINS:
                        skipped += 1
                        continue

                    inserted = self.database.insert_email(
                        mail.EntryID,
                        str(mail.SentOn),
                        recipient.Name,
                        email,
                        domain,
                        mail.Subject,
                    )

                    if inserted:
                        imported += 1
                    else:
                        skipped += 1

            except Exception:
                skipped += 1

        return imported, skipped

    @staticmethod
    def _get_recipient_email(recipient):
        try:
            address_entry = recipient.AddressEntry

            if address_entry.Type == "EX":
                exchange_user = address_entry.GetExchangeUser()

                if exchange_user:
                    return exchange_user.PrimarySmtpAddress or ""

                return address_entry.Address or ""

            return address_entry.Address or ""

        except Exception:
            try:
                return recipient.Address or ""
            except Exception:
                return ""

    @staticmethod
    def _get_domain(email):
        if "@" not in email:
            return ""

        return email.rsplit("@", 1)[1].strip().lower()
